# ruff: noqa: E501  (data-heavy seed script: long word/example lines are fine)
"""Add a new domain='統計学'(statistics) vocabulary set, authored by Claude
(2026-08-04・ユーザー要望:「統計学...も必要かな」).

このDBには既存のAI/ML語彙(domain='AI'や'数学')に機械学習寄りの用語
(gradient boosting, linear regression, overfitting等)は既にあるが、
統計学そのものを扱うdomainは一件も存在しなかった(要確認済み: domain LIKE
'%統計%' で0件)。本スクリプトは研究・ビジネスのデータ分析で使う古典的・
基礎的な統計学用語を新設のdomain='統計学'として追加する。

重複チェック: 追加前に既存語彙(6330件, english小文字)と全候補語を突合し、
以下は既存語(別domain)と完全一致するため除外した:
  median(交通), standard deviation(数学), variance(数学), outlier(数学),
  skewness(数学), degrees of freedom(機械工学), correlation(論文用語),
  average(数学), distribution(数学), covariance(数学), probability(数学),
  regression(AI), sample(既存), parameter(既存), control group(既存)

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_statistics.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 基本統計量(代表値・散布度) ---
    ("mean", "平均値", "名詞", "The mean of the five test scores was 82 points.", "統計学", "400"),
    ("mode", "最頻値", "名詞", "The mode of the dataset is the value that appears most frequently.", "統計学", "500"),
    ("range", "範囲(最大値と最小値の差)", "名詞", "The range of the dataset is the difference between the highest and lowest values.", "統計学", "450"),
    ("weighted average", "加重平均", "名詞", "Her final grade was a weighted average of the exam, homework, and participation scores.", "統計学", "600"),
    ("moving average", "移動平均", "名詞", "Analysts often use a 50-day moving average to smooth out short-term price fluctuations.", "統計学", "650"),
    ("z-score", "z得点", "名詞", "A z-score tells you how many standard deviations a value is from the mean.", "統計学", "750"),
    ("percentile", "パーセンタイル", "名詞", "Her score placed her in the 90th percentile nationwide.", "統計学", "650"),
    ("quartile", "四分位数", "名詞", "The data was divided into quartiles to compare the top and bottom performers.", "統計学", "700"),
    ("interquartile range", "四分位範囲", "名詞", "The interquartile range is less sensitive to outliers than the full range.", "統計学", "800"),
    ("kurtosis", "尖度", "名詞", "High kurtosis indicates that the data has more extreme outliers than a normal distribution.", "統計学", "950"),
    ("bell curve", "釣鐘型曲線・ベルカーブ", "名詞", "Exam scores often form a bell curve, with most students clustered around the average.", "統計学", "550"),
    # --- 分布 ---
    ("normal distribution", "正規分布", "名詞", "Human height roughly follows a normal distribution.", "統計学", "600"),
    ("standard normal distribution", "標準正規分布", "名詞", "We converted the raw scores into a standard normal distribution with a mean of 0 and a standard deviation of 1.", "統計学", "800"),
    ("probability distribution", "確率分布", "名詞", "The probability distribution shows how likely each outcome is.", "統計学", "700"),
    ("frequency distribution", "度数分布", "名詞", "The frequency distribution lists how many times each value occurs in the dataset.", "統計学", "600"),
    ("cumulative distribution", "累積分布", "名詞", "The cumulative distribution shows the proportion of values at or below a given point.", "統計学", "800"),
    ("binomial distribution", "二項分布", "名詞", "The number of heads in ten coin flips follows a binomial distribution.", "統計学", "800"),
    ("Poisson distribution", "ポアソン分布", "名詞", "The number of customer complaints per day can be modeled with a Poisson distribution.", "統計学", "850"),
    ("central limit theorem", "中心極限定理", "名詞", "The central limit theorem explains why sample means tend to follow a normal distribution as sample size grows.", "統計学", "900"),
    ("expected value", "期待値", "名詞", "The expected value of the lottery ticket was lower than its price.", "統計学", "700"),
    # --- 標本抽出・推測統計 ---
    ("sample size", "標本サイズ・サンプルサイズ", "名詞", "A larger sample size generally produces more reliable results.", "統計学", "550"),
    ("sample mean", "標本平均", "名詞", "The sample mean was close to the population mean, suggesting the sample was representative.", "統計学", "650"),
    ("population mean", "母平均", "名詞", "Researchers used the sample data to estimate the population mean.", "統計学", "650"),
    ("random sampling", "無作為抽出・ランダムサンプリング", "名詞", "Random sampling ensures that every member of the population has an equal chance of being selected.", "統計学", "650"),
    ("stratified sampling", "層化抽出", "名詞", "We used stratified sampling to make sure each age group was represented proportionally.", "統計学", "800"),
    ("sampling bias", "サンプリングバイアス・標本抽出の偏り", "名詞", "Sampling bias occurred because the survey only reached smartphone users.", "統計学", "750"),
    ("descriptive statistics", "記述統計", "名詞", "Descriptive statistics summarize the basic features of a dataset.", "統計学", "600"),
    ("inferential statistics", "推測統計", "名詞", "Inferential statistics let us draw conclusions about a population from a sample.", "統計学", "700"),
    ("random variable", "確率変数", "名詞", "A random variable can take on different values depending on the outcome of a random process.", "統計学", "750"),
    ("discrete variable", "離散変数", "名詞", "The number of defective items per batch is a discrete variable.", "統計学", "700"),
    ("continuous variable", "連続変数", "名詞", "Height and weight are continuous variables that can take any value within a range.", "統計学", "700"),
    ("categorical data", "質的データ・カテゴリカルデータ", "名詞", "Gender and country of residence are examples of categorical data.", "統計学", "600"),
    # --- 仮説検定 ---
    ("hypothesis testing", "仮説検定", "名詞", "Hypothesis testing helps us decide whether an observed effect is likely due to chance.", "統計学", "750"),
    ("null hypothesis", "帰無仮説", "名詞", "The null hypothesis states that there is no difference between the two groups.", "統計学", "800"),
    ("alternative hypothesis", "対立仮説", "名詞", "If we reject the null hypothesis, we accept the alternative hypothesis instead.", "統計学", "800"),
    ("p-value", "p値", "名詞", "A p-value below 0.05 is often treated as statistically significant.", "統計学", "800"),
    ("significance level", "有意水準", "名詞", "We set the significance level at 0.05 before running the test.", "統計学", "750"),
    ("statistical significance", "統計的有意性", "名詞", "The results did not reach statistical significance, so we cannot draw firm conclusions.", "統計学", "750"),
    ("confidence interval", "信頼区間", "名詞", "The 95% confidence interval suggests the true value lies between 4.2 and 4.8.", "統計学", "750"),
    ("margin of error", "誤差の範囲・許容誤差", "名詞", "The poll has a margin of error of plus or minus three percentage points.", "統計学", "700"),
    ("t-test", "t検定", "名詞", "We ran a t-test to compare the average scores of the two groups.", "統計学", "750"),
    ("chi-square test", "カイ二乗検定", "名詞", "A chi-square test showed a significant association between the two categorical variables.", "統計学", "800"),
    ("ANOVA", "分散分析(ANOVA)", "名詞", "ANOVA let us compare the means of three or more groups at once.", "統計学", "850"),
    ("standard error", "標準誤差", "名詞", "The standard error decreases as the sample size increases.", "統計学", "750"),
    ("effect size", "効果量", "名詞", "The effect size tells us how large the difference between groups really is, beyond just significance.", "統計学", "800"),
    ("type I error", "第一種の過誤", "名詞", "A type I error occurs when we reject a true null hypothesis.", "統計学", "850"),
    ("type II error", "第二種の過誤", "名詞", "A type II error happens when we fail to reject a false null hypothesis.", "統計学", "850"),
    ("statistical power", "検定力", "名詞", "Increasing the sample size improves the statistical power of the test.", "統計学", "850"),
    # --- 相関・回帰・因果 ---
    ("correlation coefficient", "相関係数", "名詞", "The correlation coefficient between advertising spend and sales was 0.82.", "統計学", "750"),
    ("causation", "因果関係", "名詞", "Correlation does not imply causation, so we need further experiments to confirm the cause.", "統計学", "700"),
    ("regression to the mean", "平均への回帰", "名詞", "Regression to the mean can make an ineffective treatment look successful if patients were selected because their symptoms were unusually severe.", "統計学", "850"),
    ("residual", "残差", "名詞", "The residual is the difference between the observed value and the value predicted by the model.", "統計学", "800"),
    ("coefficient of determination", "決定係数", "名詞", "The coefficient of determination, or R-squared, shows how much of the variation is explained by the model.", "統計学", "900"),
    ("confounding variable", "交絡変数", "名詞", "A confounding variable, such as age, may explain the apparent link between the two factors.", "統計学", "900"),
    ("time series", "時系列", "名詞", "We analyzed the monthly sales as a time series to spot seasonal patterns.", "統計学", "700"),
    # --- 可視化 ---
    ("histogram", "ヒストグラム", "名詞", "The histogram showed that most customers were between 25 and 34 years old.", "統計学", "550"),
    ("scatter plot", "散布図", "名詞", "We used a scatter plot to visualize the relationship between price and demand.", "統計学", "550"),
    ("box plot", "箱ひげ図", "名詞", "The box plot made it easy to spot outliers in the delivery times.", "統計学", "650"),
    # --- バイアス・研究設計 ---
    ("data dredging", "データの拾い食い・恣意的な検定の繰り返し", "名詞", "Data dredging can produce misleading results by testing many hypotheses until one appears significant by chance.", "統計学", "900"),
    ("survivorship bias", "生存者バイアス", "名詞", "Survivorship bias led investors to overestimate the average return, since failed funds had already disappeared from the data.", "統計学", "850"),
    ("selection bias", "選択バイアス", "名詞", "Selection bias arose because only satisfied customers responded to the survey.", "統計学", "800"),
    ("randomized controlled trial", "ランダム化比較試験", "名詞", "The drug's effectiveness was confirmed through a randomized controlled trial.", "統計学", "800"),
    ("observational study", "観察研究", "名詞", "Unlike an experiment, an observational study does not assign subjects to treatment groups.", "統計学", "800"),
    ("placebo effect", "プラセボ効果", "名詞", "Some patients improved simply due to the placebo effect, not the medication itself.", "統計学", "700"),
]


def main() -> int:
    with db() as conn:
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        added = skipped = 0
        for en, ja, pos, ex, domain, level in WORDS:
            if en.lower() in existing:
                skipped += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, ja, pos, ex, domain, level),
            )
            existing.add(en.lower())
            added += 1
    print(f"words: +{added} (skipped {skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
