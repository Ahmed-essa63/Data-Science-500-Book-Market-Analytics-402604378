# Book Market Analytics Report

## 1. Introduction
This project collects and analyses book listing data from Books to Scrape. The objective is to explore prices, ratings and availability and demonstrate a basic regression model.

## 2. Data collection
The raw dataset contains 1000 scraped listings. The cleaned dataset contains 1000 records with identifiable titles and prices. The fields include title, price in GBP, star rating, availability, quantity where provided, and product URL where available.

## 3. Data cleaning
The analysis removes records without a usable title or price, converts prices to numeric GBP values, converts recognised star ratings to numbers from 1 to 5, and saves the result to data/processed/books_clean.csv. Missing ratings are left blank rather than invented.

## 4. Descriptive analysis
- Books retained after cleaning: 1000
- Average price: £35.07
- Median price: £36.00
- Minimum price: £10.00
- Maximum price: £59.99
- Books with recognised ratings: 1000

Price distribution chart: reports/figures/price_distribution.svg

Rating distribution chart: reports/figures/rating_distribution.svg

## 5. Linear regression
A simple ordinary least-squares linear regression uses star rating as the predictor and price in GBP as the target. Model results are saved in reports/model_metrics.json.

{
  "method": "Simple linear regression",
  "feature": "rating",
  "target": "price_gbp",
  "slope": 0.2836,
  "intercept": 34.2415,
  "r_squared": 0.0008,
  "rated_books_used": 1000,
  "example_prediction_rating_3": 35.09
}

This is an exploratory model, not evidence that a higher rating causes a higher price. Ratings alone may not explain price differences, and the model should not be used as a reliable pricing tool without further validation.

## 6. Conclusion
The collected listings provide a basic view of book prices, ratings and availability. The cleaned CSV and charts support further analysis. Future work could add book categories, compare prices between categories, and evaluate predictive accuracy on a separate test set.

## 7. References
Books to Scrape (n.d.) *Books to Scrape*. Available at: https://books.toscrape.com/ (Accessed: 23 October 2026).

Python Software Foundation (n.d.) *Python 3 Documentation*. Available at: https://docs.python.org/3/ (Accessed: 23 October 2026).
