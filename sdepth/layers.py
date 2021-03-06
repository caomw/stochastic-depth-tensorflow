"""
Layers for stochastic depth
"""


import tensorflow as tf


def conv(prev, kernel_shape, bias_shape, stride, padding, scope,
         use_relu=True):
    with tf.variable_scope(scope):
        weights = tf.get_variable('weights', kernel_shape)
        bias = tf.get_variable('biases', bias_shape)
        conv2d = tf.nn.conv2d(prev, weights, stride, padding)
        biased = tf.nn.bias_add(conv2d, bias)
        if use_relu:
            return tf.nn.relu(biased)
        else:
            return biased


def maxpool(prev, kernel_shape, stride, padding, scope):
    with tf.name_scope(scope):
        return tf.nn.max_pool(prev, kernel_shape, stride, padding)


def avgpool(prev, kernel_shape, stride, padding, scope):
    with tf.name_scope(scope):
        return tf.nn.avg_pool(prev, kernel_shape, stride, padding)


def residual_block(prev, bottleneck_depth, output_depth, survival_rate, scope):
    with tf.variable_scope(scope):
        res = prev
        prev_depth = prev.get_shape()[3].value
        if prev_depth != output_depth:
            res = conv(prev=prev,
                       kernel_shape=[1, 1, prev_depth, output_depth],
                       bias_shape=[output_depth],
                       stride=[1, 1, 1, 1],
                       padding='SAME',
                       scope='shortcut')

        def not_dropped():
            conv2d = conv(prev=prev,
                          kernel_shape=[1, 1, prev_depth, bottleneck_depth],
                          bias_shape=[bottleneck_depth],
                          padding='SAME',
                          stride=[1, 1, 1, 1],
                          scope='bottleneck_1x1')
            conv2d = conv(prev=conv2d,
                          kernel_shape=[3, 3, bottleneck_depth, bottleneck_depth],
                          bias_shape=[bottleneck_depth],
                          stride=[1, 1, 1, 1],
                          padding='SAME',
                          scope='bottleneck_3x3')
            conv2d = conv(prev=conv2d,
                          kernel_shape=[1, 1, bottleneck_depth, output_depth],
                          bias_shape=[output_depth],
                          stride=[1, 1, 1, 1],
                          padding='SAME',
                          scope='output_1x1',
                          use_relu=False)
            add = tf.add(res, conv2d)
            return tf.nn.relu(add)

        def dropped():
            return tf.nn.relu(res)

        survival_rate = tf.constant(survival_rate, name='survival_rate')
        survival_roll = tf.random_uniform(shape=[],
                                          minval=0.0,
                                          maxval=1.0,
                                          name='survival')
        survive = tf.less(survival_roll, survival_rate)
        return tf.cond(survive, not_dropped, dropped)


if __name__ == '__main__':
    inputs = tf.placeholder(tf.float32, [None, 55, 55, 64])
    output = residual_block(prev=inputs,
                            bottleneck_depth=32,
                            output_depth=128,
                            survival_rate=0.8,
                            scope='stack')
    writer = tf.train.SummaryWriter('stochastic_depth',
                                    graph=tf.get_default_graph())
    writer.close()