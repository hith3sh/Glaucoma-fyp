import tensorflow as tf
import numpy as np
import cv2
import matplotlib.pyplot as plt
import os
import uuid
GRADCAM_ASSETS_DIR = os.path.abspath('../front-end_tumor/public/assets/gradcam_assets')
os.makedirs(GRADCAM_ASSETS_DIR, exist_ok=True)
print(f"GradCAM directory created at: {GRADCAM_ASSETS_DIR}")

model = tf.keras.models.load_model('../weights/glaucoma_cnn_model.h5')

# def preprocess_image(image_bytes):
#     image = cv2.imread(image_bytes)
#     image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # Convert to RGB
#     ## crop the image
#     crop_box = (600, 300, 1600, 1200)
#     height , width = image.shape[:2]
#     if height == 1934 and width == 2576:
#         print('cropping the image')
#         x, y, w, h = crop_box
#         cropped_image = image[y:y+h, x:x+w]

#         # Normalize intensity to range [0, 255]
#         normalized_image = cv2.normalize(cropped_image, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)
#         # Convert to LAB color space
#         lab_image = cv2.cvtColor(normalized_image, cv2.COLOR_BGR2LAB)
#         # Apply CLAHE to the L channel
#         l, a, b = cv2.split(lab_image)
#         clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
#         l = clahe.apply(l)
#         # Merge the channels back
#         enhanced_image = cv2.merge((l, a, b))
#         # Convert back to BGR color space
#         enhanced_image = cv2.cvtColor(enhanced_image, cv2.COLOR_LAB2BGR)
#         image = enhanced_image
    
#     # Resize the image to match model input size
#     image = cv2.resize(image, (224, 224))
#     # Normalize to [0, 1] for model input
#     image_array = image / 255.0
#     image_array = np.expand_dims(image_array, axis=0)  # Add batch dimension
#     return image_array


def generate_gradcam(original_image, image, tabular_data, layer_name='conv2d_1'):
    try:
        # Generate a random filename using UUID
        filename = f'gradcam_{uuid.uuid4()}.png'
        output_path = os.path.join(GRADCAM_ASSETS_DIR, filename)
        
        # Create GradCAM model
        grad_model = tf.keras.models.Model(
            [model.inputs],
            [model.get_layer(layer_name).output, model.output]
        )

        # Generate gradients
        with tf.GradientTape() as tape:
            conv_outputs, predictions = grad_model([image, tabular_data])
            loss = predictions[:, np.argmax(predictions[0])]

        # Extract gradients and feature map
        grads = tape.gradient(loss, conv_outputs)
        pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
        conv_outputs = conv_outputs[0]
        
        # Generate heatmap
        heatmap = tf.reduce_mean(tf.multiply(pooled_grads, conv_outputs), axis=-1)
        heatmap = tf.maximum(heatmap, 0) / tf.math.reduce_max(heatmap)
        heatmap = heatmap.numpy()
        
        
        # Resize heatmap to match original image size
        heatmap = cv2.resize(heatmap, (224, 224))
        heatmap = np.uint8(255 * heatmap)
        heatmap = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
        
        original_image_resized = cv2.resize(original_image, (heatmap.shape[1], heatmap.shape[0]))

        # Superimpose heatmap on original image
        try:
            superimposed = cv2.addWeighted(original_image_resized, 0.6, heatmap, 0.4, 0)
        except Exception as e:
            raise e
        
        # Save the visualization
        try:
            result = cv2.imwrite(output_path, cv2.cvtColor(superimposed, cv2.COLOR_RGB2BGR))
            #-- delete from here
            # fig, axs = plt.subplots(1, 3, figsize=(15, 5))

            # # Display the original image
            # axs[0].imshow(original_image)
            # axs[0].set_title('Original Image')
            # axs[0].axis('off')  # Hide axes

            # # Display the heatmap
            # axs[1].imshow(heatmap)
            # axs[1].set_title('Heatmap')
            # axs[1].axis('off')  # Hide axes

            # # Display the superimposed image
            # axs[2].imshow(superimposed)
            # axs[2].set_title('Superimposed Image')
            # axs[2].axis('off')  # Hide axes

            # # Adjust layout
            # plt.tight_layout()
            # plt.show()
            #----- to here
            if not result:
                print("cv2.imwrite failed to save the image")
        except Exception as e:
            print(f"Error saving file: {str(e)}")
            raise e
        
        return filename

    except Exception as e:
        print(f"Error in generate_gradcam: {str(e)}")
        raise e

# Example usage:
# if __name__ == "__main__":
#     # Test the function
#     gender = 0
#     age = 42
#     rightDioptre1 =  0.737636
#     rightDioptre2 = -1.625104
#     rightAstigmatism = 92.371608
#     rightLens =0.666667
#     rightPneumatic = 16.259596
#     rightPachymetry = 536.930380
#     rightAxialLength = 23.551106
#     rightVFMD = -4.344207
#     rightEye = 1

#     right_tabular_data_arr = [
#                         age,
#                         rightDioptre1,
#                         rightDioptre2, 
#                         rightAstigmatism,
#                         rightLens,
#                         rightPneumatic,
#                         rightPachymetry,
#                         rightAxialLength,
#                         rightVFMD,
#                         gender,
#                         rightEye
#                         ]
#     right_tabular_data = np.array([right_tabular_data_arr], dtype=np.float32) 

#     image_path = 'cropped_image.jpg'

#     image_bytes = cv2.imread(image_path)
#     original_image = cv2.cvtColor(image_bytes, cv2.COLOR_BGR2RGB)  # Convert to RGB
    
#     left_eye_image = preprocess_image(image_path)
    
#     output_path = generate_gradcam(original_image, left_eye_image, right_tabular_data)
#     print(f"GradCAM visualization saved to: {output_path}") 

