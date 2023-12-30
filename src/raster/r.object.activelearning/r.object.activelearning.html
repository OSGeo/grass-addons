<h2>DESCRIPTION</h2>
This module uses SVM from the <em> scikit-learn </em> python package to perform
classification on regions of raster maps. These regions can be the output of
<em><a href="https://grass.osgeo.org/grass-stable/manuals/i.segment.html">i.segment</a></em>
or
<em><a href="https://grass.osgeo.org/grass-stable/manuals/r.clump.html">r.clump</a></em>.

<p>
The module enables learning with only a small initial labeled data set via
<em>active learning</em>. This semi-supervised learning algorithm interactively
query the user to label the regions that are most useful to improve the overall
classification score.  With this technique, the number of examples to learn the
classification is often much lower than the number of examples needed in normal
supervised algorithms. You should start the classification with a small training
set and run the module multiple times to label new informative samples to
improve the classification score. The score metric is the number of correctly
predicted labels over the total number of samples in the test set.

<p>
The samples that are chosen to be labeled are the ones where the class
prediction is the most uncertain [2].  Moreover, from the more uncertain
samples, only the most different samples are kept [1]. This diversity heuristic
takes into account for each uncertain sample the distance to its closest
neighbour and the average distance to all other samples. This ensures that newly
labeled samples are not redundant with each other.

<p>
The learning data should be composed of features extracted from the regions, for
example with the
<em><a href="i.segment.stats.html">i.segment.stats</a></em> module.
The features of the training set, the test set and the unlabeled set should be
in three different files in csv format. The first line of each file must be a
header containing the features' name. Every regions should be uniquely
identified by the first attribute. The classes for the training and test
examples should be the second attribute.

<p>
Example of a training and test files :
	<div class="code">
		<pre>
			cat,Class_num,attr1,attr2,attr3
			167485,4,3.546,456.76,6.76
			183234,6,5.76,1285.54,9.45
			173457,2,5.65,468.76,6.78
		</pre>
	</div>

<p>
Example of an unlabeled file :
	<div class="code">
		<pre>
			cat,attr1,attr2,attr3
			167485,3.546,456.76,6.76
			183234,5.76,1285.54,9.45
			173457,5.65,468.76,6.78
		</pre>
	</div>

<p>
The training set can be easily updated once you have labeled new samples. Create
a file to specify what label you give to which sample.
This file in csv format should have a header and two attributes per line : the
ID of the sample you have labeled and the label itself.  The module will
transfer the newly labeled samples from the unlabeled set to the training set,
adding the class you have provided. This is done internally and does not modify
your original files.

<p>
If the user wants to save the changes in new files according to the updates, new
files can be created with the new labeled samples added to the training file and
removed from the unlabeled file. Just specify the path of those output files in
the parameters (training_updated, unlabeled_updated).

<p>
Example of an update file :
	<div class="code">
		<pre>
			cat,Class_num
			194762,2
			153659,6
			178350,2
		</pre>
	</div>

<p>
Here are more details on a few parameters :
<ul>
	<li><b>learning_steps</b> : This is the number of samples that
		the module will ask to label at each run.</li>
	<li><b>nbr_uncertainty</b> : Number of uncertain samples to
		choose before applying the diversity filter. This number should
		be higher than <em>learning_steps</em></li>
	<li><b>diversity_lambda</b> : Parameter used in the diversity
		heuristic. If close to 0 only take into account the average
		distance to all other samples. If close to 1 only take into
		account the distance to the closest neighbour</li>
	<li><b>c_SVM</b> : Penalty parameter C of the error term. If
		it is too large there is a risk of overfitting the training
		data. If it is too small you may have underfitting.</li>
	<li><b>gamma_SVM</b> : Kernel coefficient. 1/#features is
		often a good value to start with.</li>
		If C or gamma is left empty (or both), a good value based on the
		data distibution is found by cross-validation (at least 3
		samples per class in the training set is needed, more is
		better). This automatic parameter tuning requires more
		computation time as the training set grows.
	<li><b>search_iter</b>  :Number of parameter settings that are
		sampled in the automatic parameter search (C, gamma).
		search_iter trades off runtime vs quality of the solution.</li>
</ul>

<h2>EXAMPLES</h2>

The following examples are based on the data files found in this module
repository.

<h3>Simple run without an update file</h3>

<div class="code">
	<pre>
		r.object.activelearning training_set=/path/to/training_set.csv \
					test_set=/path/to/test_set.csv \
					unlabeled_set=/path/to/unlabeled_set.csv

		Parameters used : C=146.398423284, gamma=0.0645567086567, lambda=0.25
		12527959
		9892568
		13731120
		15445003
		13767630
		Class predictions written to predictions.csv
		Training set : 70
		Test set : 585
		Unlabeled set : 792
		Score : 0.321367521368
	</pre>
</div>

<h3>With an update file</h3>

The five samples output at the previous example have been labeled and added to
the update file.

<div class="code">
	<pre>
		r.object.activelearning training_set=/path/to/training_set.csv \
		                        test_set=/path/to/test_set.csv \
					unlabeled_set=/path/to/unlabeled_set.csv \
					update=/path/to/update.csv

		Parameters used : C=101.580687073, gamma=0.00075388337475, lambda=0.25
		Class predictions written to predictions.csv
		Training set : 75
		Test set : 585
		Unlabeled set : 787
		Score : 0.454700854701
		8691475
		9321017
		14254774
		14954255
		15838185
	</pre>
</div>


<h2>NOTES</h2>

This module requires the <em> scikit-learn </em> python package. This module
needs to be installed in your GRASS GIS Python environment. Please refer to <a
     href="r.learn.ml.html"><em>r.learn.ml</em></a>'s notes on how to install
this package.

<p>
The memory usage for ~1450 samples of 52 features each is around ~650 kb.  This
number can vary due to the unpredictablity of the garbage collector's behaviour.
Everything is computed in memory; therefore the size of the data is limited by
the amount of RAM available.

<h2>REFERENCES</h2>
[1] Bruzzone, L. and Persello, C. (2009). Active learning for classification of
remote sensing images. 2009 IEEE International Geoscience and Remote Sensing
Symposium. doi:10.1109/igarss.2009.5417857<br>
[2] Tuia, D. et al (2011). A Survey of Active Learning Algorithms for Supervised Remote Sensing Image Classification. IEEE Journal of Selected Topics in Signal Processing, 5(3), 606-617. doi:10.1109/jstsp.2011.2139193


<h2>AUTHOR</h2>

Lucas Lef&egrave;vre (ULB, Brussels, Belgium)
