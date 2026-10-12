#include <iostream>
#include <vector>
#include <cstdlib>
#include <ctime>

#if defined(_WIN32) || defined(_WIN64)
    #include <conio.h>
    #include <windows.h>
    void delay_ms(int ms) { Sleep(ms); }
#else
    #include <unistd.h>
    #include <termios.h>
    #include <fcntl.h>
    void delay_ms(int ms) { usleep(ms * 1000); }
    
    int _kbhit() {
        struct termios oldt, newt;
        int ch, oldf;
        tcgetattr(STDIN_FILENO, &oldt);
        newt = oldt;
        newt.c_lflag &= ~(ICANON | ECHO);
        tcsetattr(STDIN_FILENO, TCSANOW, &newt);
        oldf = fcntl(STDIN_FILENO, F_GETFL, 0);
        fcntl(STDIN_FILENO, F_SETFL, oldf | O_NONBLOCK);
        ch = getchar();
        tcsetattr(STDIN_FILENO, TCSANOW, &oldt);
        fcntl(STDIN_FILENO, F_SETFL, oldf);
        if (ch != EOF) {
            ungetc(ch, stdin);
            return 1;
        }
        return 0;
    }
    char _getch() { return getchar(); }
#endif

using namespace std;

const int WIDTH = 20;
const int HEIGHT = 15;

struct Position {
    int x, y;
};

int main() {
    srand(time(0));
    int playerX = WIDTH / 2;
    vector<Position> bullets;
    vector<Position> enemies;
    int score = 0;
    bool gameOver = false;
    int enemyTimer = 0;

    cout << "=== SPACE SHOOTER ===\n";
    cout << "A: Left | D: Right | SPACE: Shoot | Q: Quit\n";
    cout << "Press any key to start...";
    _getch();

    while (!gameOver) {
        if (_kbhit()) {
            char input = _getch();
            if (input == 'a' || input == 'A') { if (playerX > 0) playerX--; }
            else if (input == 'd' || input == 'D') { if (playerX < WIDTH - 1) playerX++; }
            else if (input == ' ') { bullets.push_back({playerX, HEIGHT - 2}); }
            else if (input == 'q' || input == 'Q') { break; }
        }

        enemyTimer++;
        if (enemyTimer % 5 == 0) {
            enemies.push_back({rand() % WIDTH, 0});
        }

        for (size_t i = 0; i < bullets.size(); i++) {
            bullets[i].y--;
            if (bullets[i].y < 0) {
                bullets.erase(bullets.begin() + i);
                i--;
            }
        }

        for (size_t i = 0; i < enemies.size(); i++) {
            enemies[i].y++;
            if (enemies[i].y >= HEIGHT - 1) {
                gameOver = true;
            }
        }

        for (size_t i = 0; i < bullets.size(); i++) {
            for (size_t j = 0; j < enemies.size(); j++) {
                if (bullets[i].x == enemies[j].x && (bullets[i].y == enemies[j].y || bullets[i].y == enemies[j].y + 1)) {
                    bullets.erase(bullets.begin() + i);
                    enemies.erase(enemies.begin() + j);
                    score += 10;
                    i--;
                    break;
                }
            }
        }

        #if defined(_WIN32) || defined(_WIN64)
            system("cls");
        #else
            system("clear");
        #endif

        cout << "Score: " << score << "\n";
        for (int i = 0; i < WIDTH + 2; i++) cout << "#";
        cout << "\n";

        for (int y = 0; y < HEIGHT; y++) {
            cout << "#";
            for (int x = 0; x < WIDTH; x++) {
                bool printed = false;
                
                if (y == HEIGHT - 1 && x == playerX) {
                    cout << "^";
                    printed = true;
                }
                
                if (!printed) {
                    for (auto& b : bullets) {
                        if (b.x == x && b.y == y) {
                            cout << "|";
                            printed = true;
                            break;
                        }
                    }
                }

                if (!printed) {
                    for (auto& e : enemies) {
                        if (e.x == x && e.y == y) {
                            cout << "V";
                            printed = true;
                            break;
                        }
                    }
                }

                if (!printed) cout << " ";
            }
            cout << "#\n";
        }

        for (int i = 0; i < WIDTH + 2; i++) cout << "#";
        cout << "\n";

        delay_ms(100);
    }

    cout << "\nGAME OVER! Final Score: " << score << "\n";
    return 0;
}
