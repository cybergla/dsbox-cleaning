"""
test program for MICE, a TransformerPrimitive imputer
"""
import sys
sys.path.append("../")
def text2int(col):
    """
    convert column value from text to integer codes (0,1,2...)
    """
    return pd.DataFrame(col.astype('category').cat.codes,columns=[col.name])

import pandas as pd

from dsbox.datapreprocessing.cleaner import MICE, MiceHyperparameter

# global variables
data_name =  "data.csv"
label_name =  "targets.csv" # make sure your label target is in the second column of this file
data = pd.read_csv(data_name, index_col='d3mIndex')
missing_value_mask = pd.isnull(data)
label = text2int(pd.read_csv(label_name, index_col='d3mIndex')["Class"])
hp = MiceHyperparameter.sample()


import unittest

class TestMice(unittest.TestCase):

	def setUp(self):
		self.imputer = MICE(hyperparams=hp)

	def test_init(self):
		self.assertEqual(self.imputer._has_finished, False)
		self.assertEqual(self.imputer._iterations_done, False)

	def test_run(self):
		result = self.imputer.produce(inputs=data, timeout=10).value
		self.helper_impute_result_check(data,result)
		self.assertEqual(self.imputer._has_finished, True)
		self.assertEqual(self.imputer._iterations_done, True)

	def test_timeout(self):
		result = self.imputer.produce(inputs=data, timeout=0.00001).value
		self.assertEqual(self.imputer._has_finished, False)
		self.assertEqual(self.imputer._iterations_done, False)

	def test_noMV(self):
		"""
		test on the dataset has no missing values
		"""
		result = self.imputer.produce(inputs=data, timeout=10).value
		result2 = self.imputer.produce(inputs=result, timeout=10).value	# result contains no missing value
		
		self.assertEqual(result.equals(result2), True)

	def helper_impute_result_check(self, data, result):
		"""
		check if the imputed reuslt valid
		now, check for:
		1. contains no nan anymore
		2. orignal non-nan value should remain the same
		"""
		# check 1
		self.assertEqual(pd.isnull(result).sum().sum(), 0)

		# check 2
		# the original non-missing values must keep unchanged
		# to check, cannot use pd equals, since the imputer may convert:
		# 1 -> 1.0
		# have to do loop checking
		missing_value_mask = pd.isnull(data)
		for col_name in data:
			data_non_missing = data[~missing_value_mask[col_name]][col_name]
			result_non_missing = result[~missing_value_mask[col_name]][col_name]
			for i in data_non_missing.index:
				self.assertEqual(data_non_missing[i]==result_non_missing[i], True, 
					msg="not equals in column: {}".format(col_name))
if __name__ == '__main__':
    unittest.main()