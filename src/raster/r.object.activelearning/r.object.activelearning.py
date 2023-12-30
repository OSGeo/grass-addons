#!/usr/bin/env python
# encoding: utf-8
# ******************************************************************
# *
# * MODULE:	r.object.activelearning
# *
# * AUTHOR(S)	Lucas Lefèvre
# *
# * PURPOSE:	Active learning for classifying raster objects
# *
# * COPYRIGHT:	(C) 2017 Lucas Lefèvre, and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
# *
# ******************************************************************

# %module
# % description: Active learning for classifying raster objects
# %end
# %option G_OPT_F_INPUT
# % key: training_set
# % description: Training set (csv format)
# % required: yes
# %end
# %option G_OPT_F_INPUT
# % key: test_set
# % description: Test set (csv format)
# % required: yes
# %end
# %option G_OPT_F_INPUT
# % key: unlabeled_set
# % description: Unlabeled samples (csv format)
# % required: yes
# %end
# %option
# % key: learning_steps
# % type: integer
# % description: Number of samples to label at each iteration
# % answer: 5
# % required: no
# %end
# %option
# % key: nbr_uncertainty
# % type: integer
# % description: Number of samples to select (based on uncertainty criterion) before applying the diversity criterion.
# % answer: 15
# % required: no
# %end
# %option
# % key: diversity_lambda
# % type: double
# % description: Lambda parameter used in the diversity heuristic
# % answer: 0.25
# % required: no
# %end
# %option
# % key: c_svm
# % type: double
# % description: Penalty parameter C of the error term
# % required: no
# %end
# %option
# % key: gamma_parameter
# % type: double
# % description: Kernel coefficient
# % required: no
# %end
# %option
# % key: search_iter
# % type: integer
# % description: Number of parameter settings that are sampled in the automatic parameter search (C, gamma).
# % answer: 15
# % required: no
# %end
# %option G_OPT_F_INPUT
# % key: update
# % description: Training set update file
# % required: no
# %end
# %option G_OPT_F_OUTPUT
# % key: predictions
# % description: Output file for class predictions
# % required: no
# %end
# %option G_OPT_F_OUTPUT
# % key: training_updated
# % description: Output file for the updated training file
# % required: no
# %end
# %option G_OPT_F_OUTPUT
# % key: unlabeled_updated
# % description: Output file for the updated unlabeled file
# % required: no
# %end


try:  # You can run the tests outside of grass where those imports are not available
    import grass as grass
    import grass.script as gcore
except ImportError:
    pass

import sys


def load_data(file_path, labeled=False, skip_header=1, scale=True):

    """
    Load the data from a csv file

    :param file_path: Path to the csv data file
    :param labeled: True if the data is labeled (default=False)
    :param skip_header: Header size (in line) (default=1)
    :param scale: True if the data should be normalize (default=True)

    :type file_path: string
    :type labeled: boolean
    :type skip_header: int
    :type scale: boolean

    :return: Return 4 arrays, the features X, the IDs, the labels y and the header
    :rtype: ndarray
    """
    data = np.genfromtxt(file_path, delimiter=",", skip_header=0, dtype=None)

    header = np.array([])

    if skip_header != 0:
        header = data[0:skip_header, :]
    data = data[skip_header:, :]  # Remove header
    data = data.astype(float)

    ID = data[:, 0]  # get only row 0s
    if labeled:
        y = data[:, 1]  # get only row 1
        X = data[:, 2:]  # remove ID and label
    else:
        y = []
        X = data[:, 1:]  # remove ID

    if scale:
        X = preprocessing.scale(X)

    return X, ID, y, header


def write_result_file(ID, X_unlabeled, predictions, header, filename):
    """
    Write all samples with their ID and their class prediction in csv file. Also add the header to this csv file.

    :param ID: Samples'IDs
    :X_unlabeled: Samples'features
    :predictions: Class predictin for each sample
    :header: Header of the csv file
    :filename: Name of the csv file
    """
    data = np.copy(X_unlabeled)
    data = np.insert(data, 0, list(map(str, ID)), axis=1)
    data = np.insert(data, 1, list(map(str, predictions)), axis=1)

    if header.size != 0:
        header = np.insert(header, 1, ["Class"])
        data = np.insert(data.astype(str), 0, header, axis=0)
    np.savetxt(filename, data, delimiter=",", fmt="%s")
    return True


def update(update_file, X_train, ID_train, y_train, X_unlabeled, ID_unlabeled):
    """
    Transfer features and labels from the unlabeled arrays to the training arrays based on the update file.

    :param update_file: Path to the update file
    :param X_train: Features for the training samples
    :param ID_train: IDs of the training samples
    :param y_train: Labels of the training samples
    :param X_unlabeled: Features for the training samples
    :param ID_unlabeled: IDs of the unlabeled samples
    """
    update = np.genfromtxt(update_file, delimiter=",", skip_header=1)
    if update.size == 0:
        return X_train, ID_train, y_train
    elif update.ndim == 1:
        update = [update]
    for index_update, row in enumerate(update):
        index = np.where(
            ID_unlabeled == row[0]
        )  # Find in 'unlabeled' the line corresping to the ID
        if index[0].size != 0:  # Check if row exists
            features = X_unlabeled[index[0][0]]  # Features
            ID = ID_unlabeled[index[0][0]]
            label = row[1]
            X_train = np.append(X_train, [features], axis=0)
            ID_train = np.append(ID_train, [ID], axis=0)
            y_train = np.append(y_train, [label], axis=0)
        else:
            gcore.warning("The following sample could not be found :{}".format(row[0]))

    return X_train, ID_train, y_train


def write_update(
    update_file,
    training_file,
    unlabeled_file,
    new_training_filename,
    new_unlabeled_filename,
):
    """
    Transfer samples from the unlabeled set to the training set based on an update file
    with IDs of samples to transfer and their classes.

    :param update_file: Path to the update file
    :param training_file: Path to the training file
    :param unlabeled_file: Path to the unlabeled file
    :param new_training_filename: Path to the new training file that will be created
    :param new_unlabeled_filename: Path to the new unlabeled file that will be created

    :type update_file: string
    :type training_file: string
    :type unlabeled_file: string
    :type new_training_filename: string
    :type new_unlabeled_filename: string
    """
    update = np.genfromtxt(update_file, delimiter=",", skip_header=1)
    training = np.genfromtxt(training_file, delimiter=",", skip_header=0, dtype=None)
    unlabeled = np.genfromtxt(unlabeled_file, delimiter=",", skip_header=0, dtype=None)
    successful_updates = []

    if update.size == 0:
        return
    elif update.ndim == 1:
        update = [update]

    for index_update, row in enumerate(update):
        index = np.where(
            unlabeled == str(row[0])
        )  # Find in 'unlabeled' the line corresping to the ID
        if index[0].size != 0:  # Check if row exists
            data = unlabeled[index[0][0]][1:]  # Features
            data = np.insert(data, 0, row[0], axis=0)  # ID
            data = np.insert(data, 1, row[1], axis=0)  # Class
            training = np.append(training, [data], axis=0)
            unlabeled = np.delete(unlabeled, index[0][0], axis=0)
            successful_updates.append(index_update)
        else:
            gcore.warning(
                "Unable to update completely: the following sample could not be found in the unlabeled set:{}".format(
                    row[0]
                )
            )

    with open(update_file) as f:
        header = f.readline()
        header = header.split(",")

    update = np.delete(update, successful_updates, axis=0)
    update = np.insert(update.astype(str), 0, header, axis=0)

    # Save files
    if new_training_filename != "":
        write_updated_file(new_training_filename, training)
        gcore.message("New training file written to {}".format(new_training_filename))
    if new_unlabeled_filename != "":
        write_updated_file(new_unlabeled_filename, unlabeled)
        gcore.message("New unlabeled file written to {}".format(new_unlabeled_filename))


def write_updated_file(file_path, data):
    """
    Write to disk some csv data. Add '_updated' at the end of the filename
    :param filename: location where the file will be saved
    :param data: data to save

    :type file_path: string
    :type data: ndarray
    """

    np.savetxt(file_path, data, delimiter=",", fmt="%s")


def linear_scale(data):
    """
    Linearly scale values : 5th percentile to 0 and 95th percentile to 1

    :param data: Features
    :type data: ndarray(#samples x #features)

    :return: Linearly scaled data
    :rtype: ndarray(#samples x #features)
    """
    p5 = np.percentile(data, 5, axis=0, interpolation="nearest")[
        np.newaxis
    ]  # 5th percentiles as a 2D array (-> newaxis)
    p95 = np.percentile(data, 95, axis=0, interpolation="nearest")[
        np.newaxis
    ]  # 95th percentiles as a 2D array (-> newaxis)

    return (data - p5) / (p95 - p5)


def train(X, y, c_svm, gamma_parameter):
    """
    Train a SVM classifier.

    :param c: Penalty parameter C of the error term.
    :param gamma: Kernel coefficient
    :param X: Features of the training samples
    :param y: Labels of the training samples

    :return: Returns the trained classifier
    :rtype: sklearn.svm.SVC
    """
    classifier = svm.SVC(
        kernel="rbf",
        C=c_svm,
        gamma=gamma_parameter,
        probability=False,
        decision_function_shape="ovr",
        random_state=1938475632,
    )
    classifier.fit(X, y)

    return classifier


def active_diversity_sample_selection(X_unlabled, nbr, classifier):
    """
    Select a number of samples to label based on uncertainety and diversity

    :param X_unlabeled: Pool of unlabeled samples
    :param nbr: Number of samples to select from the pool
    :param classifier: Used to predict the class of each sample

    :type X_unlabeled: ndarray(#samples x #features)
    :type nbr: int
    :type classifier: sklearn.svm.SVC

    :return: Indexes of selected samples
    :rtype: ndarray
    """

    batch_size = (
        nbr_uncertainty  # Number of samples to select with the uncertainty criterion
    )

    uncertain_samples_index = uncertainty_filter(
        X_unlabled, batch_size, classifier
    )  # Take twice as many samples as needed
    uncertain_samples = X_unlabled[uncertain_samples_index]

    return diversity_filter(
        uncertain_samples, uncertain_samples_index, nbr, diversity_lambda
    )


def uncertainty_filter(samples, nbr, classifier):
    """
    Keep only a few samples based on an uncertainty criterion
    Return the indexes of samples to keep

    :param samples: Pool of unlabeled samples to select from
    :param nbr: number of samples to select from the pool
    :param classifier: Used to predict the class of each sample

    :type X_unlabeled: ndarray(#samples x #features)
    :type nbr: int
    :type classifier: sklearn.svm.SVC

    :return: Indexes of selected samples
    :rtype: ndarray
    """
    NBR_NEW_SAMPLE = nbr
    decision_function = np.absolute(classifier.decision_function(samples))

    # Check if the number of samples to return is not
    # bigger than the total number of samples
    if nbr >= samples.shape[0]:
        NBR_NEW_SAMPLE = samples.shape[0] - 1

    # Get the max distance to each class hyperplane for each example
    max_index = np.argmax(decision_function[:, :], axis=1)
    max_values = decision_function[np.arange(len(decision_function)), max_index]

    # Make the max values very small.
    # The max value is now the second best
    decision_function[np.arange(len(decision_function)), max_index] = np.NINF

    # Get the second max distance to each class to hyperplane for each example
    second_max_index = np.argmax(decision_function[:, :], axis=1)
    second_max_values = decision_function[
        np.arange(len(decision_function)), second_max_index
    ]

    # "Functionnal margin" for multiclass classifiers for each sample
    f_MC = max_values - second_max_values

    selected_sample_index = np.argpartition(f_MC, NBR_NEW_SAMPLE)[:NBR_NEW_SAMPLE]

    return selected_sample_index


def diversity_filter(samples, uncertain_samples_index, nbr, diversity_lambda=0.25):
    """
    Keep only 'nbr' samples based on a diversity criterion (bruzzone2009 : Active Learning For Classification Of Remote Sensing Images)
    Return the indexes of samples to keep

    :param samples: Pool of unlabeled samples
    :param uncertain_samples: Indexes of uncertain samples in the arry of samples
    :param nbr: number of samples to select from the pool
    :param diversity_lambda: Heuristic parameter, between 0 and 1. Weight between the average distance to other samples and the distance to the closest sample. (default=0.25)

    :type X_unlabeled: ndarray(#samples x #features)
    :type uncertain_samples_index: ndarray(#uncertain_samples)
    :type nbr: int
    :type diversity_lambda: float

    :return: Indexes of selected samples
    :rtype: ndarray
    """
    L = diversity_lambda
    m = samples.shape[0]  # Number of samples
    samples_cpy = np.empty(samples.shape)
    samples_cpy[:] = samples

    selected_sample_index = uncertain_samples_index  # At the begining, take all samples

    while selected_sample_index.shape[0] > nbr:

        dist_to_closest = distance_to_closest(samples_cpy)
        average_dist = average_distance(samples_cpy)
        discard = np.argmax(L * dist_to_closest + (1 - L) * (1.0 / m) * average_dist)
        selected_sample_index = np.delete(
            selected_sample_index, discard
        )  # Remove the sample to discard
        samples_cpy = np.delete(samples_cpy, discard, axis=0)

    return selected_sample_index


def distance_to_closest(samples):
    """
    For each sample, computes the distance to its closest neighbour

    :param samples: Samples to consider
    :type samples: ndarray(#samples x #features)

    :return: For each sample, the distance to its closest neighbour
    :rtype: ndarray(#samples)
    """
    dist_with_samples = rbf_kernel(
        samples, samples
    )  # Distance between each samples (symetric matrix)
    np.fill_diagonal(
        dist_with_samples, np.NINF
    )  # Do not take into acount the distance between a sample and itself (values on the diagonal)
    dist_with_closest = dist_with_samples.max(
        axis=0
    )  # For each sample, the distance to the closest other sample

    return dist_with_closest


def average_distance(samples):
    """
    For each sample, computes the average distance to all other samples

    :param samples: Samples to consider
    :type samples: ndarray(#samples x #features)

    :return: For each sample, the average distance to all other samples
    :rtype: ndarray(#samples)
    """
    samples = np.asarray(samples)
    nbr_samples = samples.shape[0]
    dist_with_samples = rbf_kernel(samples, samples)
    average_dist = (dist_with_samples.sum(axis=1) - 1) / (
        nbr_samples - 1
    )  # Remove dist to itself (=1)

    return average_dist


def learning(
    X_train, y_train, X_test, y_test, X_unlabeled, ID_unlabeled, steps, sample_selection
):
    """
    Train a SVM classifier with the training data, compute the score of the classifier based on testing data and
    make a class prediction for each sample in the unlabeled data.
    Find the best samples to label that would increase the most the classification score

    :param X_train: Features of training samples
    :param y_train: Labels of training samples
    :param X_test: Features of test samples
    :param y_test: Labels of test samples
    :param X_unlabeled: Features of unlabeled samples
    :param ID_unlabeled: IDs of unlabeled samples
    :param steps: Number of samples to label
    :param sample_selection: Function used to select the samples to label (different heuristics)

    :type X_train: ndarray(#samples x #features)
    :type y_train: ndarray(#samples)
    :type X_test: ndarray(#samples x #features)
    :type y_test: ndarray(#samples)
    :type X_unlabeled: ndarray(#samples x #features)
    :type ID_unlabeled: ndarray(#samples)
    :type steps: int
    :type samples_selection: callable

    :return: The IDs of samples to label, the score of the classifier and the prediction for all unlabeled samples
    :rtype indexes: ndarray(#steps)
    :rtype score: float
    :rtype predictions: ndarray(#unlabeled_samples)
    """

    if X_unlabeled.size == 0:
        raise Exception("Pool of unlabeled samples empty")

    c_svm, gamma_parameter = SVM_parameters(
        options["c_svm"], options["gamma_parameter"], X_train, y_train, search_iter
    )
    gcore.message(
        "Parameters used : C={}, gamma={}, lambda={}".format(
            c_svm, gamma_parameter, diversity_lambda
        )
    )

    classifier = train(X_train, y_train, c_svm, gamma_parameter)
    score = classifier.score(X_test, y_test)

    predictions = classifier.predict(X_unlabeled)

    samples_to_label = sample_selection(X_unlabeled, steps, classifier)

    return ID_unlabeled[samples_to_label], score, predictions


def SVM_parameters(c, gamma, X_train, y_train, n_iter):
    """
    Determine the parameters (C and gamma) for the SVM classifier.
    If a parameter is specified in the parameters, keep this value.
    If it is not specified, compute the 'best' value by grid search (cross validation set)

    :param c: Penalty parameter C of the error term.
    :param gamma: Kernel coefficient
    :param X_train: Features of the training samples
    :param y_train: Labels of the training samples
    :param n_iter: Number of parameter settings that are sampled. n_iter trades off runtime vs quality of the solution.

    :type c: string
    :type gamma: string
    :type X_train: ndarray
    :type Y_train: ndarray
    :type n_iter: int

    :return: The c and gamma parameters
    :rtype: floats
    """

    parameters = {}
    if c == "" or gamma == "":
        parameters = {
            "C": scipy.stats.expon(scale=100),
            "gamma": scipy.stats.expon(scale=0.1),
            "kernel": ["rbf"],
            "class_weight": ["balanced", None],
        }

    if parameters != {}:
        svr = svm.SVC()
        clf = RandomizedSearchCV(svr, parameters, n_iter=n_iter, n_jobs=-1, verbose=0)
        clf.fit(X_train, y_train)

    if c == "":
        c = clf.best_params_["C"]
    if gamma == "":
        gamma = clf.best_params_["gamma"]
    return float(c), float(gamma)


def main():
    global learning_steps
    global diversity_lambda
    global nbr_uncertainty
    global search_iter

    global svm, preprocessing, train_test_split, RandomizedSearchCV
    global StratifiedKFold, rbf_kernel
    try:
        from sklearn import svm
        from sklearn import preprocessing
        from sklearn.model_selection import train_test_split
        from sklearn.model_selection import RandomizedSearchCV
        from sklearn.model_selection import StratifiedKFold
        from sklearn.metrics.pairwise import rbf_kernel
    except ImportError:
        gcore.fatal(
            "This module requires the scikit-learn python package. Please install it."
        )

    global scipy, np
    try:
        import scipy
        import numpy as np
    except ModuleNotFoundError as e:
        msg = e.msg
        gcore.fatal(
            _(
                "Unable to load python <{0}> lib (requires lib "
                "<{0}> being installed).".format(msg.split("'")[-2])
            )
        )

    learning_steps = (
        int(options["learning_steps"]) if options["learning_steps"] != "0" else 5
    )
    search_iter = (
        int(options["search_iter"]) if options["search_iter"] != "0" else 10
    )  # Number of samples to label at each iteration
    diversity_lambda = (
        float(options["diversity_lambda"])
        if options["diversity_lambda"] != ""
        else 0.25
    )  # Lambda parameter used in the diversity heuristic
    nbr_uncertainty = (
        int(options["nbr_uncertainty"]) if options["nbr_uncertainty"] != "0" else 15
    )  # Number of samples to select (based on uncertainty criterion) before applying the diversity criterion. Must be at least greater or equal to [LEARNING][steps]

    X_train, ID_train, y_train, header_train = load_data(
        options["training_set"], labeled=True
    )
    X_test, ID_test, y_test, header_test = load_data(options["test_set"], labeled=True)
    X_unlabeled, ID_unlabeled, y_unlabeled, header_unlabeled = load_data(
        options["unlabeled_set"]
    )

    nbr_train = ID_train.shape[0]

    if (
        options["update"] != ""
    ):  # If an update file has been specified, transfer samples
        X_train, ID_train, y_train = update(
            options["update"], X_train, ID_train, y_train, X_unlabeled, ID_unlabeled
        )
        if options["training_updated"] != "" or options["unlabeled_updated"] != "":
            write_update(
                options["update"],
                options["training_set"],
                options["unlabeled_set"],
                options["training_updated"],
                options["unlabeled_updated"],
            )
    elif options["update"] == "" and (
        options["training_updated"] != "" or options["unlabeled_updated"] != ""
    ):
        gcore.warning("No update file specified : could not write the updated files.")
    nbr_new_train = ID_train.shape[0]

    samples_to_label_IDs, score, predictions = learning(
        X_train,
        y_train,
        X_test,
        y_test,
        X_unlabeled,
        ID_unlabeled,
        learning_steps,
        active_diversity_sample_selection,
    )

    X_unlabeled, ID_unlabeled, y_unlabeled, header_unlabeled = load_data(
        options["unlabeled_set"], scale=False
    )  # Load unscaled data

    predictions_file = options["predictions"]
    if (
        predictions_file != ""
    ):  # Write the class prediction only if an output file has been specified by the user
        write_result_file(
            ID_unlabeled, X_unlabeled, predictions, header_unlabeled, predictions_file
        )
        gcore.message("Class predictions written to {}".format(predictions_file))

    gcore.message("Training set : {}".format(X_train.shape[0]))
    gcore.message("Test set : {}".format(X_test.shape[0]))
    gcore.message(
        "Unlabeled set : {}".format(X_unlabeled.shape[0] - (nbr_new_train - nbr_train))
    )
    gcore.message("Score : {}".format(score))

    for ID in samples_to_label_IDs:
        print((int(ID)))


if __name__ == "__main__":
    options, flags = grass.script.parser()
    main()
