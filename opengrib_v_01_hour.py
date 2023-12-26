import os
import pygrib
import h5py
import numpy as np

# Get a list of all files in the folder
def TransGrib2H5(folder_path):
    file_list = [f for f in os.listdir(folder_path) if f.endswith('.grib2')]
    output_file_paths = []

    for hour_value in range(24):
        hour_str = f't{hour_value:02d}z'
        for file_name in file_list:
            parts = file_name.split('.')

            if hour_str in parts:
                # Check if corresponding .h5 file already exists
                output_file_path = os.path.join(folder_path, os.path.splitext(file_name)[0] + '.h5')
                if os.path.exists(output_file_path):
                    output_file_paths.append(output_file_path)
                    print(f"Skipping {file_name}, .h5 file already exists.")
                    continue

                # Open the GRIB file
                file_path = os.path.join(folder_path, file_name)
                grbs = pygrib.open(file_path)

                # Select and process the desired messages
                grb_list = grbs.select(name='Total Precipitation', typeOfLevel='surface')
                if grb_list:
                    for grb in grb_list:
                        # Process the GRIB message as needed
                        print(f"File: {file_name}")
                        print("Values Shape:", grb.values.shape)
                        data = grb.values
                        lats, lons = grb.latlons()

                        with h5py.File(output_file_path, 'w') as h5_file:
                            h5_file.create_dataset('fields', data=data)
                            h5_file.create_dataset('lats', data=lats)
                            h5_file.create_dataset('lons', data=lons)

                        print(f'save to: {output_file_path}')
                        output_file_paths.append(output_file_path)
                else:
                    print(f"No matching messages found for {file_name}")
                grbs.close()

    return output_file_paths



idx=0
data_idx=0
def CropH5(path1,func1,path2,func2):

    #define crop function
    global idx
    global data_idx
    # data_idx = idx  * 16
    print(data_idx)
    print(f'Processing image dateset__{path1}\n{path2}')
    with h5py.File(path1, 'r') as read_fixed_file,h5py.File(path2, 'r') as read_moving_file:

        # Crop the fields_data to the center
        fixed_fields_dataset = read_fixed_file['fields']
        moving_fields_dataset = read_moving_file['fields']
        fixed_fields_data = fixed_fields_dataset[:]
        moving_fields_data = moving_fields_dataset[:]
        start_row = (fixed_fields_data.shape[0] - 1052) // 2
        start_col = (fixed_fields_data.shape[1] - 1788) // 2
        end_row = start_row + 1052
        end_col = start_col + 1788
        fixed_fields_data = fixed_fields_data[start_row:end_row, start_col:end_col]
        moving_fields_data = moving_fields_data[start_row:end_row, start_col:end_col]

        # padding
        pad_amount = ((2, 2), (2, 2))
        fixed_fields_data = np.pad(fixed_fields_data, pad_amount, 'constant')
        moving_fields_data = np.pad(moving_fields_data, pad_amount, 'constant')
        print('Shape of fields_data',fixed_fields_data.shape)

        # Crop the fields_data to 16*66*112
        m, n = fixed_fields_data.shape
        block_width = n // 16
        block_height = m // 16

        # 循环切割数组
        for i in range(16):
            for j in range(16):
                # 计算当前小块的起始和结束索引
                start_row = i * block_height
                end_row = start_row + block_height
                start_col = j * block_width
                end_col = start_col + block_width

                # 切割并存储当前小块
                fixed_cropped_block = fixed_fields_data[start_row:end_row, start_col:end_col]
                moving_cropped_block = moving_fields_data[start_row:end_row, start_col:end_col]

                # calculating average
                row_average = [sum(row) / len(row) for row in fixed_cropped_block]
                average = sum(row_average) / len(row_average)

                if average>=0.01:
                    print(f'average of {path1} is {average}')

                    # 使用 data_idx 作为数据集索引
                    dataset_name = f'data_{data_idx}'
                    func1.create_dataset(dataset_name, data=fixed_cropped_block)
                    func2.create_dataset(dataset_name, data=moving_cropped_block)
                    data_idx += 1



result_file_path = 'moving.h5'
fixed_file_path = 'fixed.h5'
def readH5(filepaths):
    global idx
    global data_idx
    with h5py.File(fixed_file_path, 'w') as fixed_file,h5py.File(result_file_path, 'w') as result_file:
        for i, file_path in enumerate(file_paths):

            # creating 01-error-correcting dateset
            if 'f00' in file_path:
                moving_name_split = os.path.basename(file_path).split('.')
                a = list(moving_name_split[2])
                if 0< int(a[2]) <= 24:
                    b = f't0{int(a[2]) - 1}z'
                    corresponding_file_path = os.path.join(folder_path, f"{moving_name_split[0]}."
                                                                        f"{moving_name_split[1]}.{b}.wrfprsf01.h5")
                    if os.path.exists(corresponding_file_path):
                        CropH5(file_path, fixed_file,corresponding_file_path,result_file)
                        idx+=1

    # Load the data from fixed.h5 into a numpy array
    with h5py.File(fixed_file_path, 'r') as fixed_file:
        fixed_data = np.array([fixed_file[f'data_{i}'][:] for i in range(data_idx)])

    # Load the data from result.h5 into a numpy array
    with h5py.File(result_file_path, 'r') as result_file:
        result_data = np.array([result_file[f'data_{i}'][:] for i in range(data_idx)])

    print(f'Shape of moving_data: {result_data.shape}','\n',result_data,)
    print(f'Shape of fixed_data: {fixed_data.shape}','\n',fixed_data)

if __name__ == '__main__':
    # Specify the folder containing the GRIB files
    folder_path = 'D:/registration/TransMorph_Transformer_for_Medical_Image_Registration-main/dataset/03' ## Grib2 文件存放路径
    file_paths = TransGrib2H5(folder_path)
    readH5(file_paths)
