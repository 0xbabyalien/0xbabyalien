#include <iostream>
#include <vector>
#include <ctime>
#include <cstdlib>
#include <algorithm>
#include <chrono>
#include <random>
using namespace std;

#ifdef _WIN32
    #include <conio.h>
    #include <windows.h>
    void sleepMs(int ms) { Sleep(ms); }
    bool keyPressed()   { return _kbhit(); }
    int  getKey()       { return _getch(); }
#else
    #include <termios.h>
    #include <unistd.h>
    #include <sys/select.h>
    void sleepMs(int ms) { usleep(ms * 1000); }
    bool keyPressed() {
        timeval tv = {0, 0};
        fd_set fds; FD_ZERO(&fds);
        FD_SET(STDIN_FILENO, &fds);
        return select(STDIN_FILENO + 1, &fds, NULL, NULL, &tv) > 0;
    }
    int getKey() {
        termios oldt, newt;
        tcgetattr(STDIN_FILENO, &oldt);
        newt = oldt; newt.c_lflag &= ~(ICANON | ECHO);
        tcsetattr(STDIN_FILENO, TCSANOW, &newt);
        int ch = getchar();
        if (ch == 27 && keyPressed()) {
            getchar();
            int arrow = getchar();
            tcsetattr(STDIN_FILENO, TCSANOW, &oldt);
            switch (arrow) {
                case 'A': return 'w';
                case 'B': return 's';
                case 'C': return 'd';
                case 'D': return 'a';
            }
        }
        tcsetattr(STDIN_FILENO, TCSANOW, &oldt);
        return ch;
    }
#endif

const int W = 10, H = 20;

const int SHAPES[7][4][2] = {
    {{0,1},{1,1},{2,1},{3,1}},
    {{1,0},{2,0},{1,1},{2,1}},
    {{1,0},{0,1},{1,1},{2,1}},
    {{1,0},{2,0},{0,1},{1,1}},
    {{0,0},{1,0},{1,1},{2,1}},
    {{0,0},{0,1},{1,1},{2,1}},
    {{2,0},{0,1},{1,1},{2,1}},
};
const char* NAMES[7]  = {"I","O","T","S","Z","J","L"};
const int   COLORS[7] = {36, 33, 35, 32, 31, 34, 37};

int board[H][W] = {};
int cur, nxt, rot = 0, px = 3, py = 0;
long score = 0;
int totalLines = 0;
bool gameOver = false;
vector<int> bag;
int ti = 0;

int getType() {
    if (ti >= (int)bag.size()) {
        bag = {0,1,2,3,4,5,6};
        shuffle(bag.begin(), bag.end(), mt19937(rand()));
        ti = 0;
    }
    return bag[ti++];
}

vector<pair<int,int>> cells(int type, int r) {
    vector<pair<int,int>> v;
    for (int i = 0; i < 4; i++) v.push_back({SHAPES[type][i][0], SHAPES[type][i][1]});
    for (int k = 0; k < r; k++)
        for (auto& p : v) p = {3 - p.second, p.first};
    return v;
}

bool collides(int type, int r, int x, int y) {
    for (auto [dx, dy] : cells(type, r)) {
        int bx = x + dx, by = y + dy;
        if (bx < 0 || bx >= W || by >= H) return true;
        if (by >= 0 && board[by][bx]) return true;
    }
    return false;
}

int clearLines() {
    int n = 0;
    for (int y = H - 1; y >= 0; y--) {
        bool full = true;
        for (int x = 0; x < W; x++) if (!board[y][x]) full = false;
        if (full) {
            n++;
            for (int yy = y; yy > 0; yy--)
                for (int x = 0; x < W; x++) board[yy][x] = board[yy-1][x];
            for (int x = 0; x < W; x++) board[0][x] = 0;
            y++;
        }
    }
    return n;
}

void lockPiece() {
    for (auto [dx, dy] : cells(cur, rot)) {
        if (py + dy < 0) { gameOver = true; return; }
        board[py + dy][px + dx] = cur + 1;
    }
    int n = clearLines();
    static const int POINTS[5] = {0, 40, 100, 300, 1200};
    score += (long)POINTS[n] * (totalLines / 10 + 1);
    totalLines += n;

    cur = nxt; nxt = getType();
    rot = 0; px = 3; py = 0;
    if (collides(cur, rot, px, py)) gameOver = true;
}

void tryRotate() {
    int newRot = (rot + 1) % 4;
    for (int dx : {0, -1, 1, -2, 2})
        if (!collides(cur, newRot, px + dx, py)) { rot = newRot; px += dx; return; }
}

int getSpeed() {
    int level = totalLines / 10;
    return max(60, 750 - level * 60);
}

void draw() {
    cout << "\033[2J\033[H";
    cout << "========== TETRIS ==========\n";
    cout << "Score: " << score << "\n";
    cout << "Lines: " << totalLines << "  Level: " << totalLines / 10 + 1 << "\n\n";

    cout << "Next: " << NAMES[nxt] << "\n";
    auto v = cells(nxt, 0);
    for (int y = 0; y < 4; y++) {
        cout << "  ";
        for (int x = 0; x < 4; x++) {
            bool exists = false;
            for (auto [dx, dy] : v) if (dx == x && dy == y) exists = true;
            if (exists) cout << "\033[" << COLORS[nxt] << "m[]\033[0m";
            else        cout << "  ";
        }
        cout << "\n";
    }
    cout << "\n";

    auto active = cells(cur, rot);
    for (int y = 0; y < H; y++) {
        cout << "|";
        for (int x = 0; x < W; x++) {
            int val = board[y][x];
            for (auto [dx, dy] : active)
                if (px + dx == x && py + dy == y) val = cur + 1;
            if (val) cout << "\033[" << COLORS[val-1] << "m[]\033[0m";
            else     cout << " .";
        }
        cout << "|\n";
    }
    cout << string(W * 2 + 2, '=') << "\n";
    cout << "A/D Move  W Rotate  S Soft Drop  Space Hard Drop  P Pause  X Quit\n" << flush;
}

bool processInput(int k) {
    switch (k)Berikut adalah kode C++ Tetris yang seluruh teks (UI/CLI) dan variabelnya sudah diubah ke dalam bahasa Inggris, serta semua tag *comment* telah dihilangkan sepenuhnya:

```cpp
#include <iostream>
#include <vector>
#include <ctime>
#include <cstdlib>
#include <algorithm>
#include <chrono>
#include <random>
using namespace std;

#ifdef _WIN32
    #include <conio.h>
    #include <windows.h>
    void sleepMs(int ms) { Sleep(ms); }
    bool keyPressed()   { return _kbhit(); }
    int  getKey()       { return _getch(); }
#else
    #include <termios.h>
    #include <unistd.h>
    #include <sys/select.h>
    void sleepMs(int ms) { usleep(ms * 1000); }
    bool keyPressed() {
        timeval tv = {0, 0};
        fd_set fds; FD_ZERO(&fds);
        FD_SET(STDIN_FILENO, &fds);
        return select(STDIN_FILENO + 1, &fds, NULL, NULL, &tv) > 0;
    }
    int getKey() {
        termios oldt, newt;
        tcgetattr(STDIN_FILENO, &oldt);
        newt = oldt; newt.c_lflag &= ~(ICANON | ECHO);
        tcsetattr(STDIN_FILENO, TCSANOW, &newt);
        int ch = getchar();
        if (ch == 27 && keyPressed()) {
            getchar();
            int arrow = getchar();
            tcsetattr(STDIN_FILENO, TCSANOW, &oldt);
            switch (arrow) {
                case 'A': return 'w';
                case 'B': return 's';
                case 'C': return 'd';
                case 'D': return 'a';
            }
        }
        tcsetattr(STDIN_FILENO, TCSANOW, &oldt);
        return ch;
    }
#endif

const int W = 10, H = 20;

const int SHAPES[7][4][2] = {
    {{0,1},{1,1},{2,1},{3,1}},
    {{1,0},{2,0},{1,1},{2,1}},
    {{1,0},{0,1},{1,1},{2,1}},
    {{1,0},{2,0},{0,1},{1,1}},
    {{0,0},{1,0},{1,1},{2,1}},
    {{0,0},{0,1},{1,1},{2,1}},
    {{2,0},{0,1},{1,1},{2,1}},
};
const char* NAMES[7]  = {"I","O","T","S","Z","J","L"};
const int   COLORS[7] = {36, 33, 35, 32, 31, 34, 37};

int board[H][W] = {};
int cur, nxt, rot = 0, px = 3, py = 0;
long score = 0;
int totalLines = 0;
bool gameOver = false;
vector<int> bag;
int bagIndex = 0;

int getType() {
    if (bagIndex >= (int)bag.size()) {
        bag = {0,1,2,3,4,5,6};
        shuffle(bag.begin(), bag.end(), mt19937(rand()));
        bagIndex = 0;
    }
    return bag[bagIndex++];
}

vector<pair<int,int>> cells(int type, int r) {
    vector<pair<int,int>> v;
    for (int i = 0; i < 4; i++) v.push_back({SHAPES[type][i][0], SHAPES[type][i][1]});
    for (int k = 0; k < r; k++)
        for (auto& p : v) p = {3 - p.second, p.first};
    return v;
}

bool collides(int type, int r, int x, int y) {
    for (auto [dx, dy] : cells(type, r)) {
        int bx = x + dx, by = y + dy;
        if (bx < 0 || bx >= W || by >= H) return true;
        if (by >= 0 && board[by][bx]) return true;
    }
    return false;
}

int clearLines() {
    int n = 0;
    for (int y = H - 1; y >= 0; y--) {
        bool full = true;
        for (int x = 0; x < W; x++) if (!board[y][x]) full = false;
        if (full) {
            n++;
            for (int yy = y; yy > 0; yy--)
                for (int x = 0; x < W; x++) board[yy][x] = board[yy-1][x];
            for (int x = 0; x < W; x++) board[0][x] = 0;
            y++;
        }
    }
    return n;
}

void lock() {
    for (auto [dx, dy] : cells(cur, rot)) {
        if (py + dy < 0) { gameOver = true; return; }
        board[py + dy][px + dx] = cur + 1;
    }
    int n = clearLines();
    static const int POINTS[5] = {0, 40, 100, 300, 1200};
    score += (long)POINTS[n] * (totalLines / 10 + 1);
    totalLines += n;

    cur = nxt; nxt = getType();
    rot = 0; px = 3; py = 0;
    if (collides(cur, rot, px, py)) gameOver = true;
}

void tryRotate() {
    int newRot = (rot + 1) % 4;
    for (int dx : {0, -1, 1, -2, 2})
        if (!collides(cur, newRot, px + dx, py)) { rot = newRot; px += dx; return; }
}

int getSpeed() {
    int level = totalLines / 10;
    return max(60, 750 - level * 60);
}

void draw() {
    cout << "\033[2J\033[H";
    cout << "========== TETRIS ==========\n";
    cout << "Score: " << score << "\n";
    cout << "Lines: " << totalLines << "  Level: " << totalLines / 10 + 1 << "\n\n";

    cout << "Next: " << NAMES[nxt] << "\n";
    auto v = cells(nxt, 0);
    for (int y = 0; y < 4; y++) {
        cout << "  ";
        for (int x = 0; x < 4; x++) {
            bool exists = false;
            for (auto [dx, dy] : v) if (dx == x && dy == y) exists = true;
            if (exists) cout << "\033[" << COLORS[nxt] << "m[]\033[0m";
            else        cout << "  ";
        }
        cout << "\n";
    }
    cout << "\n";

    auto active = cells(cur, rot);
    for (int y = 0; y < H; y++) {
        cout << "|";
        for (int x = 0; x < W; x++) {
            int val = board[y][x];
            for (auto [dx, dy] : active)
                if (px + dx == x && py + dy == y) val = cur + 1;
            if (val) cout << "\033[" << COLORS[val-1] << "m[]\033[0m";
            else     cout << " .";
        }
        cout << "|\n";
    }
    cout << string(W * 2 + 2, '=') << "\n";
    cout << "A/D move  W rotate  S soft drop  Space hard drop  P pause  X exit\n" << flush;
}

bool processInput(int k) {
    switch (k) {
        case 'a': case 'A': if (!collides(cur, rot, px - 1, py)) px--; break;
        case 'd': case 'D': if (!collides(cur, rot, px + 1, py)) px++; break;
        case 's': case 'S':
            if (!collides(cur, rot, px, py + 1)) py++;
            else lock();
            break;
        case 'w': case 'W': tryRotate(); break;
        case ' ':
            while (!collides(cur, rot, px, py + 1)) py++;
            lock();
            break;
        case 'p': case 'P':
            cout << "\n--- PAUSED - press any key ---";
            while (!keyPressed()) sleepMs(50);
            getKey();
            break;
        case 'x': case 'X': return true;
    }
    return false;
}

int main() {
    srand(time(0));
    cout << "\033[2J\033[H";
    cout << "=============================\n";
    cout << "         TETRIS C++          \n";
    cout << "=============================\n";

    char playAgain = 'y';
    while (playAgain == 'y' || playAgain == 'Y') {
        for (auto& row : board) for (auto& c : row) c = 0;
        score = 0; totalLines = 0; gameOver = false; bagIndex = 0;
        cur = getType(); nxt = getType();
        rot = 0; px = 3; py = 0;
        draw();

        while (!gameOver) {
            auto t0 = chrono::steady_clock::now();
            int interval = getSpeed();
            while (true) {
                if (keyPressed() && processInput(getKey())) { gameOver = true; break; }
                auto elapsed = chrono::duration_cast<chrono::milliseconds>(
                                chrono::steady_clock::now() - t0).count();
                if (elapsed >= interval) break;
                sleepMs(5);
            }
            if (gameOver) break;
            if (!collides(cur, rot, px, py + 1)) py++;
            else lock();
            draw();
        }

        cout << "\n===== GAME OVER =====\n";
        cout << "Final score : " << score << "\n";
        cout << "Total lines : " << totalLines << "\n";
        cout << "\nPlay again? (y/n): ";
        cin >> playAgain;
        cin.ignore(1000, '\n');
    }
    cout << "\nThank you for playing!\n";
    return 0;
}
