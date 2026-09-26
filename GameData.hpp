#pragma once
#include <string>
#include <vector>

struct Genre {
    std::string id;
    std::wstring name;
    int cost;
    int unlockRp;
    std::vector<std::string> bestThemes;
    int wCode, wDesign, wSound;
    std::wstring desc;
};

struct Theme {
    std::string id;
    std::wstring name;
    int unlockRp;
};

struct Platform {
    std::string id;
    std::wstring name;
    int cost;
    double audienceShare;
    int unlockRp;
};

struct EngineModule {
    std::string id;
    std::wstring name;
    int cost;
    double mult;
    int rp;
};

struct CustomEngine {
    std::string id;
    std::wstring name;
    double mult;
    std::vector<std::wstring> modules;
    bool isProprietary;
};

struct Office {
    std::string id;
    std::wstring name;
    int capacity;
    int rent;
    int price;
    std::wstring desc;
};

struct Employee {
    int id;
    std::wstring name;
    std::wstring role;
    int code;
    int design;
    int sound;
    int salary;
    int morale;
    int avatarColorIdx;
};

struct Candidate {
    int id;
    std::wstring name;
    std::wstring role;
    int code;
    int design;
    int sound;
    int salary;
    int hireCost;
    int avatarColorIdx;
};

struct TechResearch {
    std::string id;
    std::wstring title;
    std::wstring desc;
    int rpCost;
    bool unlocked;
    std::wstring category;
};

struct ReleasedGame {
    long long id;
    std::wstring title;
    std::wstring genre;
    std::wstring theme;
    std::wstring platform;
    std::wstring engine;
    std::string monetization; // "premium", "f2p", "mmo"
    double score;
    long long copiesSold;
    long long revenue;
    int weeksOnMarket;
    int price;
    double marketingMultiplier;
    int dlcCount;
    long long audiencePool;
};

struct Achievement {
    std::string id;
    std::wstring title;
    std::wstring desc;
    int rewardCash;
    int rewardRp;
    bool unlocked;
};

struct BugTarget {
    float x, y;
    float size;
    bool alive;
};
