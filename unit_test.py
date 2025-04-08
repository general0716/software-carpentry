import unittest
import lazor_project_final


class TestStringMethods(unittest.TestCase):
    '''
    This test module use 'mad_1.bff'
    '''

    def test_read(self):
        '''
        This function can test the read funciton.
        '''
        fullgrid = [['x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x'],
                    ['x', 'o', 'x', 'o', 'x', 'o', 'x', 'o', 'x'],
                    ['x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x'],
                    ['x', 'o', 'x', 'o', 'x', 'o', 'x', 'o', 'x'],
                    ['x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x'],
                    ['x', 'o', 'x', 'o', 'x', 'o', 'x', 'o', 'x'],
                    ['x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x'],
                    ['x', 'o', 'x', 'o', 'x', 'o', 'x', 'o', 'x'],
                    ['x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x']]
        grid = [['o', 'o', 'o', 'o'],
                ['o', 'o', 'o', 'o'],
                ['o', 'o', 'o', 'o'],
                ['o', 'o', 'o', 'o']]
        A_blocks = 2
        B_blocks = 0
        C_blocks = 1
        lazorlist = [[2, 7, 1, -1]]
        holelist = [[3, 0], [4, 3], [2, 5], [4, 7]]
        self.assertEqual(lazor_project_final.read_bff(
            'mad_1.bff'), (fullgrid, A_blocks, B_blocks, C_blocks, lazorlist, holelist, grid))

    def test_solve(self):
        '''
        This function can test the grid in coordinate
        '''
        fullgrid = [['x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x'],
                    ['x', 'o', 'x', 'o', 'x', 'o', 'x', 'o', 'x'],
                    ['x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x'],
                    ['x', 'o', 'x', 'o', 'x', 'o', 'x', 'o', 'x'],
                    ['x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x'],
                    ['x', 'o', 'x', 'o', 'x', 'o', 'x', 'o', 'x'],
                    ['x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x'],
                    ['x', 'o', 'x', 'o', 'x', 'o', 'x', 'o', 'x'],
                    ['x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x']]
        A_blocks = 2
        B_blocks = 0
        C_blocks = 1
        lazorlist = [[2, 7, 1, -1]]
        holelist = [[3, 0], [4, 3], [2, 5], [4, 7]]
        position = [[0]]
        solved_grid = [['x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x'],
                       ['x', 'o', 'x', 'o', 'x', 'C', 'x', 'o', 'x'],
                       ['x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x'],
                       ['x', 'o', 'x', 'o', 'x', 'o', 'x', 'A', 'x'],
                       ['x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x'],
                       ['x', 'A', 'x', 'o', 'x', 'o', 'x', 'o', 'x'],
                       ['x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x'],
                       ['x', 'o', 'x', 'o', 'x', 'o', 'x', 'o', 'x'],
                       ['x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x']]
        self.assertEqual(lazor_project_final.find_path(grid=fullgrid, A_num=A_blocks, B_num=B_blocks,
                        C_num=C_blocks, lazorlist=lazorlist, holelist=holelist, position=position)[2], solved_grid)

    def test_path(self):
        '''
        This function can test the lazor path
        '''
        lazor_path = [[[2, 7, 1, -1], [3, 6, 1, -1], [4, 5, 1, -1],
                       [5, 4, 1, -1], [6, 3, 1, -1], [5, 2, -1, -1],
                       [5, 2, -1, 1], [4, 3, -1, 1], [3, 4, -1, 1],
                       [2, 5, -1, 1], [3, 6, 1, 1], [4, 7, 1, 1],
                       [5, 8, 1, 1]], [[4, 1, -1, -1], [3, 0, -1, -1]]]
        self.assertEqual(lazor_project_final.solver(
            'mad_1.bff')[1], lazor_path)

    def test_permu(self):
        '''
        This function can test the filled in permutation of blocks
        '''
        permu = ['o', 'o', 'C', 'o', 'o', 'o', 'o',
                 'A', 'A', 'o', 'o', 'o', 'o', 'o', 'o', 'o']
        self.assertEqual(lazor_project_final.solver('mad_1.bff')[2], permu)

    def test_answ(self):
        '''
        This funciton can test the result
        '''
        answ = [['o', 'o', 'C', 'o'], ['o', 'o', 'o', 'A'],
                ['A', 'o', 'o', 'o'], ['o', 'o', 'o', 'o']]
        self.assertEqual(lazor_project_final.solver('mad_1.bff')[0], answ)


if __name__ == '__main__':
    unittest.main()