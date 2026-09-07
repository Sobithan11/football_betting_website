# ⚽ Football Betting Website

A full-stack football betting web application built with Django, designed to provide a **gamified betting experience without using real money**. Users can predict football match outcomes using virtual points, track their performance and compete with other users through a leaderboard.

The project combines football data, gamification and community features to create an interactive football platform while removing the financial risk associated with traditional betting.

---

## 📌 Project Purpose

The purpose of this project is to recreate the competitive and engaging aspects of football betting without requiring users to gamble with real money. Users are given virtual points which they can use to make predictions, with their success affecting their points balance and overall ranking.

The application also provides football news and social features, making it more than just a betting simulator and allowing users to interact with other football fans.

---

## ✨ Features

### 👤 User Accounts & Profiles

Users can create accounts and log in to access personalised features. Each user has a profile containing information such as their favourite team, virtual points balance, betting statistics and betting history.

Django's authentication system is used to manage user accounts and ensure personalised information is associated with the correct user.

### ⚽ Fixtures & Virtual Betting

Users can view upcoming football fixtures and relevant match information retrieved from an external football API. They can then select matches and make predictions using their virtual points.

The application records each bet in the database and updates the user's points and statistics based on the outcome of their predictions.

### 📊 Betting History & Leaderboard

Users can view their personalised betting history to track previous predictions and performance over time. A leaderboard also allows users to compare their virtual points and performance against other users, adding a competitive element to the application.

### 📰 Personalised Football News

Users can select a favourite football team and view the latest news relating to that team. The application uses an external news API to retrieve relevant articles, providing users with personalised content based on their selected team.

### 💬 Community Discussions

The application includes a discussion system where users can create threads and communicate with other members of the community. This allows users to discuss football-related topics and share their opinions beyond the betting functionality.

---

## 🛠️ Technical Overview

The application is built using **Python and Django**, with HTML, CSS and JavaScript used to create the frontend. Django handles the main backend logic, URL routing, user authentication and communication between the frontend, database and external APIs.

The application uses **Django's ORM** to manage its relational database. Models are used to represent users, profiles, football matches, bets, betting statistics and discussion functionality, with relationships between models allowing data such as betting history and points balances to be associated with individual users.

### 🔌 API Integration

External REST APIs are used to provide dynamic football and news data. The football API provides information such as fixtures, match results and betting odds, while a news API is used to retrieve the latest articles for users' selected teams.

API credentials are stored using environment variables and excluded from version control rather than being included directly in the source code.

---

## 🗄️ Database

The application uses a relational database managed through Django's ORM. Database models allow the application to store and retrieve user accounts, profiles, matches, bets, points, statistics and community discussions.

Django migrations were used throughout development to manage changes to the database structure as new functionality was introduced.

---

## 💻 Technologies

- **Python**
- **Django**
- **HTML / CSS**
- **JavaScript**
- **Django ORM**


