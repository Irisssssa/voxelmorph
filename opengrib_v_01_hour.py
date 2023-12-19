import os
import pygrib
import h5py
import numpy as np
import pickle

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


def CropH5(file_paths):
    result_file_path = 'moving.h5'
    fixed_file_path = 'fixed.h5'

    with h5py.File(result_file_path, 'w') as result_file, h5py.File(fixed_file_path, 'w') as fixed_file:
        data_index_result = 0  # Record the index of data for result.h5
        data_index_fixed = 0   # Record the index of data for fixed.h5

        for i, file_path in enumerate(file_paths):
            # with h5py.File(file_path, 'r') as file:
            #     print(f'Processing {file_path}...')
            #     fields_dataset = file['fields']
            #     fields_data = fields_dataset[:]
            #
            # start_row = (fields_data.shape[0] - 1052) // 2
            # start_col = (fields_data.shape[1] - 1788) // 2
            # end_row = start_row + 1052
            # end_col = start_col + 1788
            #
            # # Crop the fields_data to the center
            # fields_data = fields_data[start_row:end_row, start_col:end_col]

            #creating 01-error-correcting dateset
            if 'f01' in file_path :
                moving_name_split = os.path.basename(file_path).split('.')
                a = list(moving_name_split[2])
                if int(a[2]) <= 23:
                    with h5py.File(file_path, 'r') as file:
                        print(f'Processing result image dateset__{file_path}')

                        # Crop the fields_data to the center
                        fields_dataset = file['fields']
                        fields_data = fields_dataset[:]
                        start_row = (fields_data.shape[0] - 1052) // 2
                        start_col = (fields_data.shape[1] - 1788) // 2
                        end_row = start_row + 1052
                        end_col = start_col + 1788
                        fields_data = fields_data[start_row:end_row, start_col:end_col]
                        result_file.create_dataset(f'data_{data_index_result}', data=fields_data)
                        data_index_result += 1
                        b = f't0{int(a[2]) + 1}z '
                        corresponding_file_path=os.path.join(folder_path, moving_name_split[0]+
                                                                 '.'+moving_name_split[1]+','+b+'.wrfprsf00.h5')
                        fixed_file.create_dataset(f'data_{data_index_fixed}', data=fields_data)
                        data_index_fixed+=1


    # Load the data from result.h5 into a numpy array
    with h5py.File(result_file_path, 'r') as result_file:
        result_data = np.array([result_file[f'data_{i}'][:] for i in range(data_index_result)])

    # Load the data from fixed.h5 into a numpy array
    with h5py.File(fixed_file_path, 'r') as fixed_file:
        fixed_data = np.array([fixed_file[f'data_{i}'][:] for i in range(data_index_fixed)])

    print(f'Shape of moving_data: {result_data.shape}','\n',result_data,)
    print(f'Shape of fixed_data: {fixed_data.shape}','\n',fixed_data)

if __name__ == '__main__':
    # Specify the folder containing the GRIB files
    folder_path = 'D:/registration/TransMorph_Transformer_for_Medical_Image_Registration-main/dataset/03' ## Grib2 文件存放路径
    file_paths = TransGrib2H5(folder_path)
    CropH5(file_paths)
