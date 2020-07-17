import matplotlib.pyplot as plt
import numpy as np


def show_image(collection, labels=None, fig_size=(12, 12)):
    W_grid = 4
    L_grid = 4
    grid_size = W_grid * L_grid

    if len(collection) > grid_size:
        collection = collection[:grid_size - 1]

    L_grid = math.ceil(len(collection) / W_grid)

    fig, axes = plt.subplots(L_grid, W_grid, figsize=fig_size)
    axes = axes.ravel()

    for i in np.arange(0, L_grid * W_grid):
        img = collection[i]

        if len(img.shape) == 4:
            # remove the last dimension
            img = img[0, ...]

        axes[i].imshow(img)
        if labels:
            axes[i].set_title(labels[i])

        axes[i].axis('off')

    ones = np.ones((2, 1, 3))

    show_image([ones])