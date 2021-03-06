"""
test program for GreedyImputation, a SupervisedLearnerPrimitive imputer
"""
import sys
sys.path.append("../")
def text2int(col):
    """
    convert column value from text to integer codes (0,1,2...)
    """
    return pd.DataFrame(col.astype('category').cat.codes,columns=[col.name])

import pandas as pd

from dsbox.datapreprocessing.cleaner import GreedyImputation, GreedyHyperparameter

# global variables
data_name =  "data.csv"
label_name =  "targets.csv" # make sure your label target is in the second column of this file
data = pd.read_csv(data_name, index_col='d3mIndex')
missing_value_mask = pd.isnull(data)
label = text2int(pd.read_csv(label_name, index_col='d3mIndex')["Class"])
hp = GreedyHyperparameter.sample()

import unittest

class TestMean(unittest.TestCase):
	def setUp(self):
		self.enough_time = 100
		self.not_enough_time = 0.0001

	def test_init(self):
		"""
		test if the init status is correct;
		note: 
			for SupervisedLearnerPrimitive, it is different than TransformerPrimitive. The 
			original status is all "True". This is for the imputer instance that has not been fitted
			but `set_params()`, can also directly `produce()` <- see test_run() part2
		"""
		imputer = GreedyImputation(hyperparams=hp)
		self.assertEqual(imputer._has_finished, True)
		self.assertEqual(imputer._iterations_done, True)

	def test_run(self):
		"""
		normal usage run test
		"""
		# part 1
		imputer = GreedyImputation(hyperparams=hp)
		imputer.set_training_data(inputs=data, outputs=label)	
		imputer.fit(timeout=self.enough_time)
		self.assertEqual(imputer._has_finished, True)
		self.assertEqual(imputer._iterations_done, True)

		result = imputer.produce(inputs=data, timeout=self.enough_time).value
		self.helper_impute_result_check(data, result)

		# part2: test set_params()
		imputer2 = GreedyImputation(hyperparams=hp)
		imputer2.set_params(params=imputer.get_params())
		self.assertEqual(imputer._has_finished, True)
		self.assertEqual(imputer._iterations_done, True)

		result2 = imputer2.produce(inputs=data, timeout=self.enough_time).value
		self.assertEqual(result2.equals(result), True)	# two imputers' results should be same
		self.assertEqual(imputer._has_finished, True)
		self.assertEqual(imputer._iterations_done, True)


	def test_timeout(self):
		imputer = GreedyImputation(hyperparams=hp)
		imputer.set_training_data(inputs=data, outputs=label)	
		imputer.fit(timeout=self.not_enough_time)
		self.assertEqual(imputer._has_finished, False)
		self.assertEqual(imputer._iterations_done, False)

		with self.assertRaises(ValueError):
			result = imputer.produce(inputs=data, timeout=self.not_enough_time).value
		

	def test_noMV(self):
		"""
		test on the dataset has no missing values
		"""
		imputer = GreedyImputation(hyperparams=hp)

		imputer.set_training_data(inputs=data, outputs=label)	
		imputer.fit(timeout=self.enough_time)
		result = imputer.produce(inputs=data, timeout=self.enough_time).value
		# 1. check produce(): `result` contains no missing value
		result2 = imputer.produce(inputs=result, timeout=self.enough_time).value

		self.assertEqual(result.equals(result2), True)

		# 2. check fit() & get_params() try fit on no-missing-value dataset
		imputer2 = GreedyImputation(hyperparams=hp)
		imputer.set_training_data(inputs=result, outputs=label)
		imputer.fit(timeout=self.enough_time)
		print (imputer.get_params())

	def test_notAlign(self):
		"""
		test the case that the missing value situations in trainset and testset are not aligned. eg:
			`a` missing-value columns in trainset, `b` missing-value columns in testset.
			`a` > `b`, or `a` < `b`
		"""
		imputer = GreedyImputation(hyperparams=hp)
		imputer.set_training_data(inputs=data, outputs=label)	
		imputer.fit(timeout=self.enough_time)
		result = imputer.produce(inputs=data, timeout=self.enough_time).value
		# PART1: when `a` > `b`
		data2 = result.copy()
		data2["T3"] = data["T3"].copy()	# only set this column to original column, with missing vlaues
		result2 = imputer.produce(inputs=data2, timeout=self.enough_time).value
		self.helper_impute_result_check(data2, result2)

		# PART2: when `a` < `b`
		imputer = GreedyImputation(hyperparams=hp)
		imputer.set_training_data(inputs=data2, outputs=label)	
		imputer.fit(timeout=self.enough_time)
		result = imputer.produce(inputs=data, timeout=self.enough_time).value
		# data contains more missingvalue columns than data2, 
		# the imputer should triger default impute method for the column that not is trained
		self.helper_impute_result_check(data, result)

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