#include <iostream>
#include <cmath>
#include <limits>

using namespace std;

double getNumber(const string& prompt) {
    double value;
    while (true) {
        cout << prompt;
        cin >> value;
        if (cin.fail()) {
            cin.clear();
            cin.ignore(numeric_limits<streamsize>::max(), '\n');
            cout << "Invalid input. Please enter a number.\n";
        } else {
            cin.ignore(numeric_limits<streamsize>::max(), '\n');
            return value;
        }
    }
}

int getChoice() {
    int choice;
    while (true) {
        cout << "Enter your choice (0-9): ";
        cin >> choice;
        if (cin.fail() || choice < 0 || choice > 9) {
            cin.clear();
            cin.ignore(numeric_limits<streamsize>::max(), '\n');
            cout << "Invalid choice. Please try again.\n";
        } else {
            cin.ignore(numeric_limits<streamsize>::max(), '\n');
            return choice;
        }
    }
}

void showMenu() {
    cout << "\n========== CALCULATOR ==========\n";
    cout << "1. Add\n";
    cout << "2. Subtract\n";
    cout << "3. Multiply\n";
    cout << "4. Divide\n";
    cout << "5. Power\n";
    cout << "6. Square Root\n";
    cout << "7. Percentage\n";
    cout << "8. Modulus (integers)\n";
    cout << "9. Factorial\n";
    cout << "0. Exit\n";
    cout << "================================\n";
}

long long factorial(int n) {
    long long result = 1;
    for (int i = 2; i <= n; i++) result *= i;
    return result;
}

int main() {
    cout << "Welcome to the Console Calculator!\n";

    while (true) {
        showMenu();
        int choice = getChoice();

        if (choice == 0) break;

        double a, b, result;

        switch (choice) {
            case 1:
                a = getNumber("Enter first number: ");
                b = getNumber("Enter second number: ");
                result = a + b;
                cout << "Result: " << a << " + " << b << " = " << result << "\n";
                break;
            case 2:
                a = getNumber("Enter first number: ");
                b = getNumber("Enter second number: ");
                result = a - b;
                cout << "Result: " << a << " - " << b << " = " << result << "\n";
                break;
            case 3:
                a = getNumber("Enter first number: ");
                b = getNumber("Enter second number: ");
                result = a * b;
                cout << "Result: " << a << " * " << b << " = " << result << "\n";
                break;
            case 4:
                a = getNumber("Enter dividend: ");
                b = getNumber("Enter divisor: ");
                if (b == 0) {
                    cout << "Error: Division by zero is not allowed.\n";
                } else {
                    result = a / b;
                    cout << "Result: " << a << " / " << b << " = " << result << "\n";
                }
                break;
            case 5:
                a = getNumber("Enter base: ");
                b = getNumber("Enter exponent: ");
                result = pow(a, b);
                cout << "Result: " << a << " ^ " << b << " = " << result << "\n";
                break;
            case 6:
                a = getNumber("Enter number: ");
                if (a < 0) {
                    cout << "Error: Cannot compute square root of a negative number.\n";
                } else {
                    result = sqrt(a);
                    cout << "Result: sqrt(" << a << ") = " << result << "\n";
                }
                break;
            case 7:
                a = getNumber("Enter value: ");
                b = getNumber("Enter total: ");
                if (b == 0) {
                    cout << "Error: Total cannot be zero.\n";
                } else {
                    result = (a / b) * 100;
                    cout << "Result: " << a << " is " << result << "% of " << b << "\n";
                }
                break;
            case 8: {
                int x = (int)getNumber("Enter first integer: ");
                int y = (int)getNumber("Enter second integer: ");
                if (y == 0) {
                    cout << "Error: Modulus by zero is not allowed.\n";
                } else {
                    cout << "Result: " << x << " % " << y << " = " << (x % y) << "\n";
                }
                break;
            }
            case 9: {
                int n = (int)getNumber("Enter a non-negative integer: ");
                if (n < 0) {
                    cout << "Error: Factorial is not defined for negative numbers.\n";
                } else if (n > 20) {
                    cout << "Error: Number too large (overflow risk).\n";
                } else {
                    cout << "Result: " << n << "! = " << factorial(n) << "\n";
                }
                break;
            }
        }
    }

    cout << "Thank you for using the calculator. Goodbye!\n";
    return 0;
}

