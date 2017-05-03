#!/usr/bin/env python
# encoding: utf-8
import unittest
import os
import numpy as np
from sklearn.metrics.pairwise import rbf_kernel

#from r.objects.activelearning import * --> doesn't work because of the dots in the file name
import imp
open_file, file_name, description = imp.find_module('r.objects.activelearning')
al = imp.load_source('al', file_name, open_file)

def silent_remove(filename) :
	"""
		Remove the file if it exists or do nothing if it does not exists
	"""
	try :
		os.remove(filename)
	except OSerror as e :
		if e.errno != errno.ENOENT :
			raise

class Test (unittest.TestCase) :


	def test_linear_scale(self) :

		X = np.random.randint(0,100, (10,5))
		#print(X)
		X = al.linear_scale(X)
		#print(X)
		p1 = np.percentile(X, 1, interpolation='nearest', axis=0)
		p5 = np.percentile(X, 5, interpolation='nearest', axis=0)
		p95 = np.percentile(X, 95, interpolation='nearest', axis=0)
		p99 = np.percentile(X, 99, interpolation='nearest', axis=0)
		
		self.assertTrue((p1 <= 0).all())
		self.assertTrue((p5 == 0).all())
		self.assertTrue((p95 == 1).all())
		self.assertTrue((p99 >= 0).all())

		X = np.random.rand(100,100)/2
		
		X = al.linear_scale(X)
		p1 = np.percentile(X, 1, interpolation='nearest', axis=0)
		p5 = np.percentile(X, 5, interpolation='nearest', axis=0)
		p95 = np.percentile(X, 95, interpolation='nearest', axis=0)
		p99 = np.percentile(X, 99, interpolation='nearest', axis=0)
		
		self.assertTrue((p1 <= 0).all())
		self.assertTrue((p5 == 0).all())
		self.assertTrue((p95 == 1).all())
		self.assertTrue((p99 >= 0).all())

	def test_dist_to_closest(self) :
		# 5 samples
		a = [1, 	3]
		b = [0, 	4]
		c = [2, 	5]
		d = [-1, 	2]
		e = [-1, 	2]
		samples = np.array([a, b, c, d, e])

		dist = al.distance_to_closest(samples)
		self.assertEqual(dist[0], rbf_kernel([a], [b])[0][0]) # closest to a
		self.assertEqual(dist[1], rbf_kernel([b], [a])[0][0]) # closest to b
		self.assertEqual(dist[2], rbf_kernel([c], [b])[0][0]) # closest to c
		self.assertEqual(dist[3], rbf_kernel([d], [e])[0][0]) # closest to d
		self.assertEqual(dist[4], rbf_kernel([d], [e])[0][0]) # closest to e


	def test_average_dist(self) :
		# 3 samples
		a = [1, 	3]
		b = [0, 	4]
		c = [2, 	5]
		samples = np.array([a, b, c])
		dist = al.average_distance(samples)

		avg_a = (rbf_kernel([a], [b])[0][0] + rbf_kernel([a], [c])[0][0])/2
		avg_b = (rbf_kernel([b], [a])[0][0] + rbf_kernel([b], [c])[0][0])/2
		avg_c = (rbf_kernel([c], [a])[0][0] + rbf_kernel([c], [b])[0][0])/2
		
		self.assertAlmostEqual(dist[0],avg_a)
		self.assertAlmostEqual(dist[1],avg_b)
		self.assertAlmostEqual(dist[2],avg_c)

	def test_diversity_criterion(self) :
		# 9 samples -> plot them for a better visualization (e.g. with GeoGebra)
		a = [2, 	4]
		b = [4, 	1]
		b_bis = [4, 	1]
		c = [-2, 	1]
		d = [-1, 	5]
		e = [1.6, 	3.6]
		f = [3, 	1]
		g = [1, 	2]
		h = [9, 	5]
		i = [49, 	4] # This sample is not sent to the diversity filter
		samples = np.array([a, b, b_bis, c, d, e, f, g, h, i])

		selected_samples = al.diversity_filter(samples, np.arange(9), 4)

		self.assertTrue(0 not in selected_samples)
		self.assertTrue((1 in selected_samples) ^ (2 in selected_samples))	# Either b or b_bis is kept
		self.assertTrue(3 in selected_samples)
		self.assertTrue(4 in selected_samples)
		self.assertTrue(5 not in selected_samples)
		self.assertTrue(6 not in selected_samples)
		self.assertTrue(7 not in selected_samples)
		self.assertTrue(8 in selected_samples)

		self.assertTrue((samples == np.array([a, b, b_bis, c, d, e, f, g, h, i])).all())	# Check that the original array was not modified


	def test_write_result_file(self) :
		X = np.array([
			[11., 3.5, 4.7],
			[22., 4.5, 6.7]
		])
		header = np.array(['ID', 'attr1','attr2', 'attr3'])
		ID = np.array([1., 2.])
		predictions = np.array([0,1])
		filename = 'unittest_prediction.csv'

		#ID, X_unlabeled, predictions, header, filename

		al.write_result_file(ID, X, predictions, header, filename)

		result = np.genfromtxt(filename, delimiter=',', dtype=str)

		data = np.array([
			['ID', 'Class', 'attr1','attr2', 'attr3'],
			[1., 0., 11., 3.5, 4.7],
			[2., 1., 22., 4.5, 6.7]
		])

		self.assertTrue((data == result).all())

		silent_remove(filename)

	def test_update(self) :
		#Create a fake update file
		update_file = 'update.csv'
		update_data = np.array([
			['cat', 'Class'],
			[123, 1],
			[456, 2]
		])

		np.savetxt(update_file, update_data, delimiter=",",fmt="%s")
		X_train = np.array([
			[1,2,3],
			[4,5,6]
		])
		ID_train = np.array([111,222])
		y_train = np.array([1,2])

		X_unlabeled = np.array([
			[11,22,33],
			[44,55,66],
			[77,88,99]
		])
		ID_unlabeled = np.array([123,456, 789])

		####
		X_train, ID_train, y_train = al.update(update_file, X_train, ID_train, y_train, X_unlabeled, ID_unlabeled)
		####
		X_train_should_be = np.array([
			[1,2,3],
			[4,5,6],
			[11,22,33],
			[44,55,66]
		])

		ID_train_should_be = np.array([111,222,123,456])
		y_train_should_be = np.array([1,2,1,2])

		self.assertTrue((X_train == X_train_should_be).all())
		self.assertTrue((ID_train_should_be == ID_train).all())
		self.assertTrue((y_train_should_be == y_train).all())

		silent_remove(update_file)

	

if __name__ == '__main__' :
	unittest.main()