"""
Script containing useful functions for Jigsaw CNN
"""
import numpy as np
from itertools import product
import dataLoader as load
import math
# On server
fixed_dir = "/hepgpu3-data1/dmcsween/DataTwoWay128/fixed"
moving_dir = "/hepgpu3-data1/dmcsween/DataTwoWay128/moving"
dvf_dir = "/hepgpu3-data1/dmcsween/DataTwoWay128/DVF"


class JigsawMaker:
    def __init__(self, input_array, number_cells_per_dim=4, dims=3):
        self.cell_num = number_cells_per_dim**dims
        self.cell_shape = input_array.shape[1:4]/4
        # self.max_hamming_set =  # Calc this
        self.total_permutations = math.factorial(self.cell_num)


def average_pix(input_image):
    # Average along batch axis
    return np.mean(input_image, axis=0)


def divide_input(input_array, number_cells_per_dim=4, dims=3):
    # Key should be cube position
    # Value is sliced array
    total_cells = number_cells_per_dim**dims
    sliced_x, sliced_y, sliced_z = input_array.shape[1:4]/number_cells_per_dim
    cells = {key: input_array[:, prod[0]:prod[0]+sliced_x, prod[1]:prod[1]+sliced_y, prod[2]:prod[2]+sliced_z, :]
             for key in range(total_cells) for prod in product(range(0, number_cells_per_dim), repeat=dims)}
    return cells


"""
def jigsaw_mix(air_threshold=3):
    dict_of_all_input_pos = {k: v for k, v in enumerate(inputs)}
    dict_no_air = {k: v for k, v in dict_of_all_input_pos.items() if v > air_threshold else None}
    # Then ignore none when shuffling
    # Dictionary useful for putting things back together
"""


def get_data(fixed_dir, moving_dir, dvf_dir):
    print('Load data to Transform')
    fixed_predict, moving_predict, dvf_label = load.data_reader(fixed_dir, moving_dir, dvf_dir)

    print('Turn into numpy arrays')
    fixed_array, fixed_affine = fixed_predict.get_data()
    moving_array, moving_affine = moving_predict.get_data()
    dvf_array, dvf_affine = dvf_label.get_data(is_image=False)
    return fixed_array


def main(argv=None):
    # Load data into arrays
    fixed_array = get_data(fixed_dir, moving_dir, dvf_dir)
    # Divide input_
    fixed_cells = divide_input(fixed_array)
    # Check shapes
    for key, val in fixed_cells.items():
        print('Cell_{} Shape:'.format(key), val.shape)


if __name__ == '__main__':
    main()
