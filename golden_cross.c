#include <stdio.h>
#include <string.h>

// 扩展版股票信息结构体
struct StockInfo {
    char ts_code[10];   // 股票代码
    char name[20];      // 股票名称
    float close;        // 今日收盘价
    float ma5;          // 5日均线值
    float ma20;         // 20日均线值
};

// 功能：检测今天是否发生金叉
// 参数：
//   today - 今日的股票数据
//   yesterday - 昨日的股票数据
// 返回：1表示金叉，0表示不是
int detectGoldenCross(struct StockInfo *today, struct StockInfo *yesterday) {
    // 金叉条件：
    // 1. 今天 MA5 > MA20（短期均线跑到长期均线上方）
    // 2. 昨天 MA5 <= MA20（昨天短期均线还在长期均线下方或相等）
    // 3. 两条均线都有效（大于0）
    
    if (today->ma5 <= 0 || today->ma20 <= 0 || yesterday->ma5 <= 0 || yesterday->ma20 <= 0) {
        return 0;  // 数据不完整，不算
    }
    
    if (today->ma5 > today->ma20 && yesterday->ma5 <= yesterday->ma20) {
        return 1;  // 金叉！
    }
    
    return 0;
}

// 功能：检测今天是否发生死叉
int detectDeathCross(struct StockInfo *today, struct StockInfo *yesterday) {
    if (today->ma5 <= 0 || today->ma20 <= 0 || yesterday->ma5 <= 0 || yesterday->ma20 <= 0) {
        return 0;
    }
    
    if (today->ma5 < today->ma20 && yesterday->ma5 >= yesterday->ma20) {
        return 1;  // 死叉！
    }
    
    return 0;
}

int main() {
    // 模拟5天的数据，测试金叉死叉检测
    struct StockInfo days[5] = {
        {"000001.SZ", "平安银行", 12.00, 11.80, 12.00},  // 第1天：MA5 < MA20
        {"000001.SZ", "平安银行", 12.10, 11.90, 11.95},  // 第2天：MA5 < MA20（接近）
        {"000001.SZ", "平安银行", 12.30, 12.05, 11.90},  // 第3天：MA5 > MA20，昨天MA5 < MA20 → 金叉！
        {"000001.SZ", "平安银行", 12.50, 12.30, 11.85},  // 第4天：MA5 > MA20（持续金叉状态）
        {"000001.SZ", "平安银行", 12.20, 12.10, 12.05},  // 第5天：MA5 > MA20，但差距缩小
    };
    
    printf("========== 金叉/死叉检测测试 ==========\n\n");
    
    for (int i = 1; i < 5; i++) {
        printf("第%d天 vs 第%d天：\n", i+1, i);
        printf("  今日 MA5=%.2f  MA20=%.2f\n", days[i].ma5, days[i].ma20);
        printf("  昨日 MA5=%.2f  MA20=%.2f\n", days[i-1].ma5, days[i-1].ma20);
        
        if (detectGoldenCross(&days[i], &days[i-1])) {
            printf("  🔔 信号：金叉！可能买入时机。\n");
        } else if (detectDeathCross(&days[i], &days[i-1])) {
            printf("  ⚠️ 信号：死叉！可能卖出时机。\n");
        } else {
            printf("  ➡️ 信号：无（均线未交叉）\n");
        }
        printf("\n");
    }
    
    printf("========================================\n");
    printf("结论：第3天发生了金叉信号。\n");
    printf("当天 MA5(%.2f) 上穿 MA20(%.2f)，\n", days[2].ma5, days[2].ma20);
    printf("短期趋势由弱转强，是技术分析中的买入参考信号。\n");
    
    return 0;
}