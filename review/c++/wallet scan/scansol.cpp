#include <iostream>
#include <iomanip>
#include <fstream>
#include <vector>
#include <string>
#include <thread>
#include <chrono>
#include <curl/curl.h>
#include <nlohmann/json.hpp>

using json = nlohmann::json;

static const int LABEL_WIDTH = 10;
static const int MINT_WIDTH  = 44;
static const std::string DIVIDER(60, '~');

static size_t WriteCb(void* contents, size_t size, size_t nmemb, std::string* out) {
    out->append((char*)contents, size * nmemb);
    return size * nmemb;
}

json rpcCall(const std::string& method, const json& params) {
    const std::string url = "https://api.mainnet-beta.solana.com";

    json body = {
        {"jsonrpc", "2.0"},
        {"id", 1},
        {"method", method},
        {"params", params}
    };

    std::string payload = body.dump();
    std::string response;

    CURL* curl = curl_easy_init();
    struct curl_slist* headers = nullptr;
    headers = curl_slist_append(headers, "Content-Type: application/json");

    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, payload.c_str());
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCb);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT, 20L);

    CURLcode res = curl_easy_perform(curl);
    curl_slist_free_all(headers);
    curl_easy_cleanup(curl);

    if (res != CURLE_OK) throw std::runtime_error(curl_easy_strerror(res));

    json out = json::parse(response);
    if (out.contains("error")) throw std::runtime_error(out["error"].dump());
    return out;
}

std::string trim(const std::string& s) {
    size_t a = s.find_first_not_of(" \t\r\n");
    if (a == std::string::npos) return "";
    size_t b = s.find_last_not_of(" \t\r\n");
    return s.substr(a, b - a + 1);
}

std::vector<std::string> loadWallets(const std::string& path) {
    std::vector<std::string> wallets;
    std::ifstream f(path);
    if (!f) throw std::runtime_error("Cannot open file: " + path);

    std::string line;
    while (std::getline(f, line)) {
        line = trim(line);
        if (line.empty() || line[0] == '#') continue;
        wallets.push_back(line);
    }
    return wallets;
}

// prints one aligned "label : value" row
void printRow(const std::string& label, const std::string& value) {
    std::cout << std::left << std::setw(LABEL_WIDTH) << label << ": " << value << "\n";
}

void scanWallet(const std::string& wallet, size_t index) {
    json bal = rpcCall("getBalance", json::array({wallet}));
    double lamports = bal["result"]["value"].get<double>();

    json tok = rpcCall("getTokenAccountsByOwner", json::array({
        wallet,
        {{"programId", "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"}},
        {{"encoding", "jsonParsed"}}
    }));

    // collect non-empty token accounts first so the count can be printed before the list
    std::vector<std::pair<std::string, std::string>> tokens;
    for (auto& acc : tok["result"]["value"]) {
        auto info = acc["account"]["data"]["parsed"]["info"];
        std::string amount = info["tokenAmount"]["uiAmountString"];
        if (amount == "0") continue;  // skip empty token accounts
        tokens.push_back({info["mint"].get<std::string>(), amount});
    }

    std::ostringstream sol;
    sol << std::fixed << std::setprecision(4) << lamports / 1e9;

    std::cout << DIVIDER << "\n";
    printRow("Wallet", std::to_string(index));
    printRow("Address", wallet);
    printRow("SOL", sol.str());
    printRow("Tokens", std::to_string(tokens.size()));

    for (size_t i = 0; i < tokens.size(); i++) {
        std::ostringstream row;
        row << std::left << std::setw(MINT_WIDTH) << tokens[i].first
            << " | " << tokens[i].second;
        printRow("Token " + std::to_string(i + 1), row.str());
    }
    std::cout << DIVIDER << "\n\n";
}

int main(int argc, char* argv[]) {
    std::string file = (argc > 1) ? argv[1] : "wallets.txt";

    curl_global_init(CURL_GLOBAL_DEFAULT);

    try {
        auto wallets = loadWallets(file);
        std::cout << "Total wallets: " << wallets.size() << "\n\n";

        for (size_t i = 0; i < wallets.size(); i++) {
            try {
                scanWallet(wallets[i], i + 1);  // i + 1 so numbering starts at 1
            } catch (const std::exception& e) {
                std::cerr << "Failed to scan wallet " << (i + 1) << " (" << wallets[i] << "): "
                          << e.what() << "\n\n";
            }
            // delay between wallets to avoid hitting the RPC rate limit
            std::this_thread::sleep_for(std::chrono::milliseconds(500));
        }
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << "\n";
        return 1;
    }

    curl_global_cleanup();
    return 0;
}
