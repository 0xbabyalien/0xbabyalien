#include <iostream>
#include <deque>
#include <cstdlib>
#include <ctime>

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
        fd_set fds;
        FD_ZERO(&fds);
        FD_SET(STDIN_FILENO, &fds);
        return select(STDIN_FILENO + 1, &fds, NULL, NULL, &tv) > 0;
    }
    int getKey() {
        termios oldt, newt;
        tcgetattr(STDIN_FILENO, &oldt);
        newt = oldt;
        newt.c_lflag &= ~(ICANON | ECHO);   
        tcsetattr(STDIN_FILENO, TCSANOW, &newt);
        int ch = getchar();
        tcsetattr(STDIN_FILENO, TCSANOW, &oldt);
        
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
        return ch;
    }
#endif

using namespace std;

const int WIDTH  = 30;   
const int HEIGHT = 15;   

struct Position {
    int x, y;
    bool operator==(const Position& p) const { return x == p.x && y == p.y; }
};

deque<Position> snake;
Position food;
int dirX = 1, dirY = 0;   
int score = 0;
bool gameOver = false;

void spawnFood() {
    while (true) {
        food = { rand() % WIDTH, rand() % HEIGHT };
        bool onSnakeBody = false;
        for (auto& s : snake)
            if (s == food) { onSnakeBody = true; break; }
        if (!onSnakeBody) return;
    }
}

void initGame() {
    snake.clear();
    snake.push_front({WIDTH / 2, HEIGHT / 2});  
    score = 0;
    dirX = 1; dirY = 0;
    gameOver = false;
    spawnFood();
}

void draw() {
    
    for (int i = 0; i < HEIGHT + 6; i++) cout << "\033[A\r";
    cout << "\033[2J\033[H"; 

    cout << "  SCORE: " << score << "   |   WASD/Arrows = move, X = quit\n";

    for (int y = -1; y <= HEIGHT; y++) {
        for (int x = -1; x <= WIDTH; x++) {
            bool body = false;
            for (auto& s : snake)
                if (s.x == x && s.y == y) { body = true; break; }

            if (x == -1 || x == WIDTH || y == -1 || y == HEIGHT)
                cout << "#";                                   
            else if (body)
                cout << (snake.front() == Position{x, y} ? "@" : "o"); 
            else if (food.x == x && food.y == y)
                cout << "*";                                   
            else
                cout << " ";
        }
        cout << "\n";
    }
    cout.flush();
}

void input() {
    if (!keyPressed()) return;
    int k = getKey();
    switch (k) {
        case 'w': case 'W': if (dirY != 1)  { dirX = 0;  dirY = -1; } break;
        case 's': case 'S': if (dirY != -1) { dirX = 0;  dirY = 1;  } break;
        case 'a': case 'A': if (dirX != 1)  { dirX = -1; dirY = 0;  } break;
        case 'd': case 'D': if (dirX != -1) { dirX = 1;  dirY = 0;  } break;
        case 'x': case 'X': gameOver = true; break;
    }
}

void update() {
    Position newHead = { snake.front().x + dirX, snake.front().y + dirY };
    if (newHead.x < 0 || newHead.x >= WIDTH ||
        newHead.y < 0 || newHead.y >= HEIGHT) {
        gameOver = true;
        return;
    }

    for (auto& s : snake)
    if (s == newHead) { gameOver = true; return; }
    snake.push_front(newHead);
    if (newHead == food) {
        score += 10;
        spawnFood();
    } else {
        snake.pop_back();   
    }
}

int main() {
    srand(time(0));
    char playAgain = 'y';

    cout << "\033[2J\033[H";
    cout << "==============================" << endl;
    cout << "          SNAKE GAME          " << endl;
    cout << "==============================" << endl;

    while (playAgain == 'y' || playAgain == 'Y') {
        initGame();
        draw();

        while (!gameOver) {
            input();
            update();
            if (!gameOver) {
                draw();
                int speed = 150 - (score / 5);  
            if (speed < 50) speed = 50;
                sleepMs(speed);
            }
        }

        cout << "\n  *** GAME OVER ***" << endl;
        cout << "  Your final score: " << score << "\n" << endl;
        cout << "  Play again? (y/n): ";
        cin >> playAgain;
        cin.ignore(1000, '\n'); 
    }

    cout << "\n  Thank you for playing!" << endl;
    return 0;
}
