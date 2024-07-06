import unittest
import tempfile
import os
import numpy as np


class TestOps(unittest.TestCase):

    def test_init(self):
        self.assertEqual(np.zeros(3).tolist(), [0, 0, 0])
        self.assertEqual(np.ones((2, 3)).tolist(), [[1, 1, 1], [1, 1, 1]])
        self.assertEqual(np.eye(2).tolist(), [[1, 0], [0, 1]])
        self.assertTrue(
            np.array_equal(
                np.zeros((4, 2, 3)), np.full((4, 2, 3), 0.0, dtype=np.float64)
            )
        )

        # [[[0. 0. 0.]
        #   [0. 0. 0.]]

        #  [[0. 0. 0.]
        #   [0. 0. 0.]]

        #  [[0. 0. 0.]
        #   [0. 0. 0.]]

        #  [[0. 0. 0.]
        #   [0. 0. 0.]]]

        data = np.random.rand(3, 5)
        self.assertTrue(data.all())
        self.assertEqual(data.shape, (3, 5))
        self.assertEqual(
            [data.size, data.dtype, data.itemsize, data.nbytes, data.ndim],
            [15, np.float64, 8, 120, 2],
        )

        with tempfile.TemporaryDirectory() as tmpdirname:
            fname = os.path.join(tmpdirname, "data.npy")
            np.save(fname, data)
            self.assertTrue(os.path.exists(fname))
            self.assertEqual(np.array_equal(data, np.load(fname)), True)

    def test_ops(self):
        x = np.array(
            [(1, 2), (3, 4)], dtype=[("a", np.int8), ("b", np.int8)]
        )  # ("a", "b") is a structured dtype
        self.assertTupleEqual(x.shape, (2,))
        self.assertEqual(x["a"].tolist(), [1, 3])
        self.assertEqual(x[0]["b"], 2)
        self.assertListEqual(x.tolist(), [(1, 2), (3, 4)])

        # View the array as a different dtype
        xv = x.view(dtype=np.int16).reshape((-1, 2))
        self.assertTupleEqual(xv.shape, (1, 2))
        self.assertListEqual(
            xv.tolist(), [[513, 1027]]
        )  # 0b00000010_00000001, 0b00000100_00000011

        np.random.seed(0)
        data = np.random.rand(3, 6)
        copied_data = data.copy()
        copied_data[0, 0] = 100
        self.assertNotEqual(data[0, 0], copied_data[0, 0])
        data.sort(axis=0)
        self.assertTrue(data[0, 0] <= data[1, 0])
        data.sort(axis=1)
        self.assertTrue(data[0, 0] <= data[0, 1])
        self.assertEqual(
            [data.max(), data.min()], [0.9636627605010293, 0.02021839744032572]
        )
        self.assertEqual(
            [data.mean(), data.mean(axis=0).tolist(), data.mean(axis=1).tolist()],
            [
                0.5546070884030709,
                [
                    0.31618103308766676,
                    0.3542451395435746,
                    0.47588928057051,
                    0.6243234776274248,
                    0.7001285570374072,
                    0.8568750425518429,
                ],
                [0.3100092087879616, 0.5827233853353978, 0.7710886710858537],
            ],
        )

        extracted = data[0]
        newdata = np.delete(data, 0, axis=0)
        newdata2 = np.insert(newdata, 0, extracted, axis=0)
        self.assertTrue(np.array_equal(data, newdata2))
        res = np.append(data, [[1], [0], [10]], axis=1)
        self.assertEqual(res.shape, (3, 7))

        concat1 = np.concatenate((data, data), axis=0)
        concat2 = np.concatenate((data, data), axis=1)
        self.assertEqual(concat1.shape, (6, 6))
        self.assertEqual(concat2.shape, (3, 12))

        splited = np.split(data, 3, axis=1)
        self.assertEqual(len(splited), 3)
        self.assertEqual(splited[0].shape, (3, 2))

        self.assertTrue(np.array_equal(data[1:3], np.array([data[1], data[2]])))
        self.assertTrue(
            np.array_equal(data[0:2, 2], np.array([data[0, 2], data[1, 2]]))
        )

        a = np.arange(10)
        self.assertEqual(
            np.where(a < 5, a, 10 * a).tolist(), [0, 1, 2, 3, 4, 50, 60, 70, 80, 90]
        )

    def test_arithmetic(self):
        pass
