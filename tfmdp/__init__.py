__version__ = '0.5.5'
__release__ = 'v0.5.5-alpha'

import tensorflow as tf
# as this code was created using TF 1.0, we need to use disable eager execution and v2 behavior
tf.compat.v1.disable_eager_execution()
tf.compat.v1.disable_v2_behavior()