import tensorflow as tf
import sys
import random
import time
import numpy as np

import labelreg.helpers as helper
import labelreg.networks as network
import labelreg.utils as util
# import labelreg.losses as loss
import labelreg.modLosses as loss

# 0 - get configs
config = helper.ConfigParser(sys.argv, 'training')

# 1 - Training data
reader_moving_image, reader_fixed_image, reader_ddf_label = helper.get_data_readers(
    config['Data']['dir_moving_image'],
    config['Data']['dir_fixed_image'],
    config['Data']['ddf_label'])

# Validation data
reader_moving_image_valid, reader_fixed_image_valid, reader_ddf_label_valid = helper.get_data_readers(
    config['Validation']['dir_moving_image'],
    config['Validation']['dir_fixed_image'],
    config['Validation']['ddf_label'])
# 2 - graph -----DATA AUGMENTATION

ph_moving_image = tf.placeholder(
    tf.float32, [config['Train']['minibatch_size']]+reader_moving_image.data_shape+[1])
ph_fixed_image = tf.placeholder(
    tf.float32, [config['Train']['minibatch_size']]+reader_fixed_image.data_shape+[1])
ph_moving_affine = tf.placeholder(tf.float32, [config['Train']['minibatch_size']]+[1, 12])
ph_fixed_affine = tf.placeholder(tf.float32, [config['Train']['minibatch_size']]+[1, 12])
input_moving_image = util.warp_image_affine(ph_moving_image, ph_moving_affine)  # data augmentation
input_fixed_image = util.warp_image_affine(ph_fixed_image, ph_fixed_affine)  # data augmentation
print(type(input_moving_image))

print("Pre Build Net")
# predicting ddf
reg_net = network.build_network(network_type=config['Network']['network_type'],
                                minibatch_size=config['Train']['minibatch_size'],
                                image_moving=ph_moving_image,
                                image_fixed=ph_fixed_image)
print("Post Build Net")
# loss
# ph_moving_label = tf.placeholder(
#     tf.float32, [config['Train']['minibatch_size']]+reader_moving_image.data_shape+[1])
# ph_fixed_label = tf.placeholder(
#     tf.float32, [config['Train']['minibatch_size']]+reader_fixed_image.data_shape+[1])
print(reader_ddf_label.data_shape)
ph_ddf_label = tf.placeholder(
    tf.float32, [config['Train']['minibatch_size']] + reader_ddf_label.data_shape + [1])
# Comment out for our purposes
# input_moving_label = util.warp_image_affine(ph_moving_label, ph_moving_affine)  # data augmentation
# input_fixed_label = util.warp_image_affine(ph_fixed_label, ph_fixed_affine)  # data augmentation
#
# warped_moving_label = reg_net.warp_image(input_moving_label)  # warp the moving label with the predicted ddf

# Warp moving image with predicted ddf_
# warped_moving_image = reg_net.warp_image(ph_moving_image)
# ------------------LOSS -------------------------------
loss_similarity, loss_regulariser = loss.build_loss(similarity_type=config['Loss']['similarity_type'],
                                                    similarity_scales=config['Loss']['similarity_scales'],
                                                    regulariser_type=config['Loss']['regulariser_type'],
                                                    regulariser_weight=config['Loss']['regulariser_weight'],
                                                    ddf_label=ph_ddf_label,
                                                    network_type=config['Network']['network_type'],
                                                    ddf=reg_net.ddf)

train_op = tf.train.AdamOptimizer(config['Train']['learning_rate']).minimize(
    loss_similarity+loss_regulariser)
# --------------------------------------------------
# utility nodes - for information only
# dice = util.compute_binary_dice(warped_moving_label, input_fixed_label)
# dist = util.compute_centroid_distance(warped_moving_label, input_fixed_label)

# 3 - training
num_minibatch_test = int(reader_ddf_label.num_data/config['Train']['minibatch_size'])
train_indices = [i for i in range(reader_ddf_label.num_data)]

# Validation
num_minibatch_valid = int(reader_ddf_label_valid.num_data/config['Validation']['minibatch_size'])
valid_indices = [i for i in range(reader_ddf_label_valid.num_data)]

saver = tf.train.Saver(max_to_keep=1)
sess = tf.Session()
sess.run(tf.global_variables_initializer())
# Tensorboard abs
# merged_summary = tf.summary.merge_all()
# writer = tf.summary.FileWriter("/hepgpu3-data1/dmcsween/MPhys/NetworkOutputs")
writer = tf.summary.FileWriter("/hepgpu3-data1/dmcsween/MPhys/NetworkOutputs", sess.graph)
writer.add_graph(sess.graph)

for step in range(config['Train']['total_iterations']):

    if step in range(0, config['Train']['total_iterations'], num_minibatch_test):
        # Train
        random.shuffle(train_indices)
        random.shuffle(valid_indices)
    test_minibatch_idx = step % num_minibatch_test
    case_indices = train_indices[
        test_minibatch_idx*config['Train']['minibatch_size']:(test_minibatch_idx+1)*config['Train']['minibatch_size']]
    label_indices = [random.randrange(reader_ddf_label.num_labels[i]) for i in case_indices]

    valid_minibatch_idx = step % num_minibatch_valid
    case_indices_valid = valid_indices[
        valid_minibatch_idx*config['Validation']['minibatch_size']:(valid_minibatch_idx+1)*config['Validation']['minibatch_size']]
    label_indices_valid = [random.randrange(
        reader_ddf_label_valid.num_labels[i]) for i in case_indices_valid]

    trainFeed = {ph_moving_image: reader_moving_image.get_data(case_indices),
                 ph_fixed_image: reader_fixed_image.get_data(case_indices),
                 ph_ddf_label: reader_ddf_label.get_data(case_indices, label_indices)
                 # ph_moving_label: reader_ddf_label.get_data(case_indices, label_indices),
                 # ph_moving_affine: helper.random_transform_generator(config['Train']['minibatch_size']),
                 # ph_fixed_affine: helper.random_transform_generator(config['Train']['minibatch_size'])
                 }
    validFeed = {ph_moving_image: reader_moving_image_valid.get_data(case_indices_valid),
                 ph_fixed_image: reader_fixed_image_valid.get_data(case_indices_valid),
                 ph_ddf_label: reader_ddf_label.get_data(case_indices_valid, label_indices_valid)
                 }

    sess.run(train_op, feed_dict=trainFeed)
    if step in range(0, config['Train']['total_iterations'], config['Train']['freq_info_print']):
        # Print info on screen
        current_time = time.asctime(time.gmtime())

        # loss_similarity_train, loss_regulariser_train, dice_train, dist_train = sess.run(
        #     [loss_similarity,
        #      loss_regulariser
        #      # ,
        #      # dice,
        #      # dist
        #      ],
        #     feed_dict=trainFeed)
        loss_similarity_train, loss_regulariser_train = sess.run(
            [loss_similarity, loss_regulariser], feed_dict=trainFeed)
        print("Loss Sim:", type(loss_similarity_train))
        training_loss_val = loss_similarity_train+loss_regulariser_train
        print("Loss_val:", training_loss_val)
        training_loss = tf.Summary(value=[tf.Summary.Value(
            tag="Training_Loss", simple_value=training_loss_val), ])
        # loss = tf.summary.scalar("Loss", loss_similarity_train)
        print("Loss:", type(training_loss))
        print('----- Training -----')
        print('Step %d [%s]: Loss=%f (similarity=%f, regulariser=%f)' %
              (step,
               current_time,
               loss_similarity_train+loss_regulariser_train,
               1-loss_similarity_train,
               loss_regulariser_train))
        # print('  Dice: %s' % dice_train)
        # print('  Distance: %s' % dist_train)
        print('  Image-label indices: %s - %s' % (case_indices, label_indices))
        writer.add_summary(training_loss, step)
        #s = sess.run(merged_summary, feed_dict=trainFeed)

    if step in range(0, config['Train']['total_iterations'], config['Validation']['freq_validation']):
        loss_similarity_valid, loss_regulariser_valid = sess.run(
            [loss_similarity, loss_regulariser], feed_dict=validFeed)
        valid_loss_val = loss_similarity_valid + loss_regulariser_valid
        print("Valid Loss:", valid_loss_val)
        valid_loss = tf.Summary(value=[tf.Summary.Value(
            tag="Valid_Loss", simple_value=valid_loss_val), ])
        writer.add_summary(valid_loss, step)

    if step in range(0, config['Train']['total_iterations'], config['Train']['freq_model_save']):
        # Save information
        save_path = saver.save(sess, config['Train']['file_model_save'], write_meta_graph=False)
        print("Model saved in: %s" % save_path)
