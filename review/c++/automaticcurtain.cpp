#include <iostream>

int main() {
    int lightLevel = 0;
    const int lightThreshold = 500;
    bool isCurtainOpen = false;

    std::cout << "=== Automatic Curtain System Simulator ===" << std::endl;
    std::cout << "Enter light level (0-1023) or -1 to exit." << std::endl;

    while (true) {
        std::cout << "\nEnter current light level: ";
        if (!(std::cin >> lightLevel) || lightLevel == -1) {
            std::cout << "Exiting simulator..." << std::endl;
            break;
        }

        std::cout << "Current Light Level: " << lightLevel << std::endl;

        // Curtain movement logic
        if (lightLevel > lightThreshold && !isCurtainOpen) {
            std::cout << "Sun is shining! Opening the curtain..." << std::endl;
            std::cout << "[MOTOR] Rotating motor to 180 degrees (OPEN)" << std::endl;
            isCurtainOpen = true;
        } 
        else if (lightLevel <= lightThreshold && isCurtainOpen) {
            std::cout << "It's getting dark. Closing the curtain..." << std::endl;
            std::cout << "[MOTOR] Rotating motor to 0 degrees (CLOSED)" << std::endl;
            isCurtainOpen = false;
        } 
        else {
            std::cout << "[STATUS] No motor movement. Curtain is currently " 
                      << (isCurtainOpen ? "OPEN." : "CLOSED.") << std::endl;
        }
    }

    return 0;
}
