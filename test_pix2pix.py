from pix2pix import *

# Restore latest checkpoint
model = Generator()
checkpoint = tf.train.Checkpoint(model)
checkpoint.restore(tf.train.latest_checkpoint(checkpoint_dir))

# Load test dataset
test_dataset = tf.data.Dataset.list_files(f'{val_path}/*.png')
test_dataset = test_dataset.map(load_image_test)
test_dataset = test_dataset.batch(BATCH_SIZE)

# Generate new images
for i, (test_input, test_target) in enumerate(test_dataset.take(1)):
    generate_images(model, test_input, test_target, save=True, save_path=f'data/png/{i}.png')

print(checkpoint)
