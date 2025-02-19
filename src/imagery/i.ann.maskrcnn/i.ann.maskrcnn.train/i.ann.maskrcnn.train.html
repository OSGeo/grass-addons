<h2>DESCRIPTION</h2>

<em>i.ann.maskrcnn.train</em> allows the user to train a Mask R-CNN model on
his own dataset. The dataset has to be prepared in a predefined structure.

<h3>DATASET STRUCTURE</h3>
<p>
Training dataset should be in the following structure:

<p>
dataset-directory
    <ul>
      <li>imagenumber
	  <ul>
          <li>imagenumber.jpg (training image)</li>
          <li>imagenumber-class1-number.png (mask for one instance of class1)</li>
          <li>imagenumber-class1-number.png (mask for another instance of class1)</li>
          <li>...</li>
	  </ul>
	  </li>
	  <li>imagenumber2
	  <ul>
         <li>imagenumber2.jpg</li>
	     <li>imagenumber2-class1-number.png (mask for one instance of class1)</li>
	     <li>imagenumber2-class2-number.png (mask for another class instance)</li>
	     <li>...</li>
      </ul>
    </ul>

<p>
The described structure of directories is required. Pictures must be *.jpg
files with 3 channels (for example RGB), masks must be *.png files consisting
of numbers between 1 and 255 (object instance) and 0s (elsewhere). A mask file
for each instance of an object should be provided separately distinguished by
the suffix number.

<h2>NOTES</h2>
<p>
If you are using initial weights (the <em>model</em> parameter), epochs are
divided into three segments. Firstly training layers 5+, then fine-tuning
layers 4+ and the last segment is fine-tuning the whole architecture.
Ending number of epochs is shown for your segment, not for the whole training.

<p>
The usage of the <em>-b</em> flag will result in an activation of batch
normalization layers training. By default, this option is set to False, as it
is not recommended to train them when using just small batches (batch is
defined by the <em>images_per_gpu</em> parameter).

<p>
If the dataset consists of images of the same size, the user may use the
<em>-n</em> flag to avoid resizing or padding of images. When the flag is not
used, images are resized to have their longer side equal to the value of the
<em>images_max_dim</em> parameter and the shorter side longer or equal to the
value of the <em>images_min_dim</em> parameter and zero-padded to be of shape
<div class="code">images_max_dim x images_max_dim</div>. It results in the fact
that even images of different sizes may be used.

<p>
After each epoch, the current model is saved. It allows the user to stop the
training when he feels satisfied with loss functions. It also allows the user to
test models even during the training (and, again, stop it even before the last
epoch).

<h2>EXAMPLES</h2>

<p>
Dataset for examples:

<p>
crops
     <ul>
        <li>000000
         <ul>
          <li>000000.jpg</li>
          <li>000000-corn-0.png</li>
          <li>000000-corn-1.png</li>
          <li>...</li>
         </ul>
        </li>
        <li>000001
         <ul>
            <li>000001.jpg</li>
            <li>000001-corn-0.png</li>
            <li>000001-rice-0.png</li>
            <li>...</li>
         </ul>
        </li>
     </ul>


<h3>Training from scratch</h3>
<p>
<div class="code"><pre>
i.ann.maskrcnn.train training_dataset=/home/user/Documents/crops classes=corn,rice logs=/home/user/Documents/logs name=crops
</pre></div>
After default number of epochs, we will get a model where the first class is
trained to detect corn fields and the second one to detect rice fields.

<p>
If we use the command with reversed classes order, we will get a model where
the first class is trained to detect rice fields and the second one to detect
corn fields.
<div class="code"><pre>
i.ann.maskrcnn.train training_dataset=/home/user/Documents/crops classes=rice,corn logs=/home/user/Documents/logs name=crops
</pre></div>

<p>
The name of the model does not have to be the same as the dataset folder but
should be referring to the task of the dataset. A good name for this one
(referring also to the order of classes) could be also this one:
<div class="code"><pre>
i.ann.maskrcnn.train training_dataset=/home/user/Documents/crops classes=rice,corn logs=/home/user/Documents/logs name=rice_corn
</pre></div>

<h3>Training from a pretrained model</h3>
<p>
We can use a pretrained model to make our training faster. It is necessary for
the model to be trained on the same channels and similar features, but it does
not have to be the same ones (e.g. model trained on swimming pools in maps can
be used for a training on buildings in maps).

<p>
A model trained on different classes (use <em>-e</em> flag to exclude head
weights).
<div class="code"><pre>
i.ann.maskrcnn.train training_dataset=/home/user/Documents/crops classes=corn,rice logs=/home/user/Documents/logs name=crops model=/home/user/Documents/models/buildings.h5 -e
</pre></div>

<p>
A model trained on the same classes.
<div class="code"><pre>
i.ann.maskrcnn.train training_dataset=/home/user/Documents/crops classes=corn,rice logs=/home/user/Documents/logs name=crops model=/home/user/Documents/models/corn_rice.h5
</pre></div>

<h3>Fine-tuning a model</h3>
<p>
It is also possible to stop your training and then continue. To continue in
the training, just use the last saved epoch as a pretrained model.
<div class="code"><pre>
i.ann.maskrcnn.train training_dataset=/home/user/Documents/crops classes=corn,rice logs=/home/user/Documents/logs name=crops model=/home/user/Documents/models/mask_rcnn_crops_0005.h5
</pre></div>

<h2>SEE ALSO</h2>

<em>
<a href="i.ann.maskrcnn.html">Mask R-CNN in GRASS GIS</a>,
<a href="i.ann.maskrcnn.detect.html">i.ann.maskrcnn.detect</a>
</em>

<h2>AUTHOR</h2>

Ondrej Pesek
