'''
Paths to files used or generated by the test harness
'''

from os import path as fp


def attelo_model_paths(lconf, rconf, fold):
    """
    Return attelo model paths
    """
    return {'attach': eval_model_path(lconf, rconf, fold, "attach"),
            'label': eval_model_path(lconf, rconf, fold, "relate"),
            'intra:attach': eval_model_path(lconf, rconf, fold, "sent-attach"),
            'intra:label': eval_model_path(lconf, rconf, fold, "sent-relate")}


def eval_data_path(lconf, ext, test_data=False):
    """
    Path to data file in the evaluation dir

    :param testing: grab the test data
    :type testing: bool
    """
    dset = lconf.testset if test_data else lconf.dataset
    return fp.join(lconf.eval_dir, "%s.%s" % (dset, ext))


def mpack_paths(lconf, test_data, stripped=False):
    """
    Tuple of paths needed to read a datapack

    * features
    * edu input
    * pairings
    * vocabulary

    :param test_data: if we should load the test data for
                      the config
    :type test_data: bool
    """
    ext = 'relations.sparse'
    core_path = eval_data_path(lconf, ext, test_data=test_data)
    return (core_path + '.edu_input',
            core_path + '.pairings',
            (core_path + '.stripped') if stripped else core_path,
            core_path + '.vocab')


def fold_dir_basename(fold):
    "Relative directory for working within a given fold"
    return "fold-%d" % fold


def fold_dir_path(lconf, fold):
    "Scratch directory for working within a given fold"
    return fp.join(lconf.scratch_dir,
                   fold_dir_basename(fold))


def combined_dir_path(lconf):
    "Scratch directory for working within the global config"
    return fp.join(lconf.scratch_dir, 'combined')


def model_basename(lconf, rconf, mtype, ext):
    "Basic filename for a model"

    if 'dialogue-acts' in mtype:
        rsubconf = rconf
    elif 'attach' in mtype:
        rsubconf = rconf.attach
    else:
        rsubconf = rconf.relate

    template = '{dataset}.{learner}.{task}.{ext}'
    return template.format(dataset=lconf.dataset,
                           learner=rsubconf.key,
                           task=mtype,
                           ext=ext)


def eval_model_path(lconf, rconf, fold, mtype):
    "Model for a given loop/eval config and fold"
    if fold is None:
        parent_dir = combined_dir_path(lconf)
    else:
        parent_dir = fold_dir_path(lconf, fold)

    bname = model_basename(lconf, rconf, mtype, 'model')
    return fp.join(parent_dir, bname)


def decode_output_basename(econf):
    "Model for a given loop/eval config and fold"
    return ".".join(["output", econf.key])


def decode_output_path(lconf, econf, fold):
    "Model for a given loop/eval config and fold"
    if fold is None:
        parent_dir = combined_dir_path(lconf)
    else:
        parent_dir = fold_dir_path(lconf, fold)
    return fp.join(parent_dir,
                   decode_output_basename(econf))


def report_dir_basename(lconf, test_data):
    """Relative directory for a report directory

    :type test_data: bool
    """
    dset = lconf.testset if test_data else lconf.dataset
    return "reports-%s" % dset


def report_parent_dir_path(lconf, fold=None):
    "Directory that a report dir would be placed in"
    if fold is None:
        return lconf.scratch_dir
    else:
        return fold_dir_path(lconf, fold)


def report_dir_path(lconf, test_data, fold=None):
    """
    Path to a score file given a parent dir.
    You'll need to tack an extension onto this

    :type test_data: bool
    """
    return fp.join(report_parent_dir_path(lconf, fold),
                   report_dir_basename(lconf, test_data))


def model_info_path(lconf, rconf, test_data, fold=None, intra=False):
    """
    Path to the model output file
    """
    template = "discr-features{grain}.{learner}.txt"
    return fp.join(report_dir_path(lconf, test_data, fold=fold),
                   template.format(grain='-sent' if intra else '',
                                   learner=rconf.key))
