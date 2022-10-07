import time
import ssd1309

# Creates a new instance of SSD1309SPI
disp = ssd1309.SSD1309SPI()

# Repeats with n equal from 1 to 9
for n in range(1, 10):
    # Clears previous drawings (if any exist)
    disp.clear()

    # Draws text at (0, 0)
    disp.text("Number: " + str(n), 0, 0)

    # Submits changes to the device
    disp.render()
    
    # Waits for 1 second
    time.sleep(1)