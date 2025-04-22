import matplotlib.pyplot as plt
from epc.tofCam660 import TOFcam660

TEST_FREQUENCIES = [16, 18, 20]  # MHz
MIN_AMPLITUDE = 100
INTEGRATION_TIME = 500  # ms

def main():
    # initialization sequence
    cam = TOFcam660()
    cam.initialize()
    cam.settings.set_minimal_amplitude(MIN_AMPLITUDE)
    cam.settings.set_integration_time(INTEGRATION_TIME)

    # get flexmod distance, amplitude and dcs
    distance = {}
    amplitude = {}
    for freq in TEST_FREQUENCIES:
        cam.settings.set_flex_mod_freq(freq)
        distance[freq], amplitude[freq] = cam.get_distance_and_amplitude()

    # get normal distance and amplitude image to compare with flexmod images
    cam.settings.set_modulation(24, 0)
    distance_norm, amplitude_norm = cam.get_distance_and_amplitude()



    # ---------------- plot results ----------------
    plt.figure(figsize=(10, 5))

    # plot flexMod distance and amplitude
    for i, freq in enumerate(TEST_FREQUENCIES):
        plt.subplot(2, 4, i+1)
        plt.title(f'Amplitude FlexMod {freq} MHz')
        plt.imshow(amplitude[freq], cmap='turbo', vmin=0, vmax=3200)
        plt.subplot(2, 4, i+5)
        plt.title(f'Distance FlexMod {freq} MHz')
        plt.imshow(distance[freq], cmap='turbo', vmin=0, vmax=5000)

    plt.subplot(2, 4, 4)
    plt.title('Amplitude normal 24Mhz')
    plt.imshow(amplitude_norm, cmap='turbo', vmin=0, vmax=3200)
    plt.colorbar(label='Amplitude (DN)')

    plt.subplot(2, 4, 8)
    plt.title('Distance normal 24Mhz')
    plt.imshow(distance_norm, cmap='turbo', vmin=0, vmax=5000)
    plt.colorbar(label='Distance (mm)')

    plt.tight_layout()
    plt.show()



if __name__ == "__main__":
    main()