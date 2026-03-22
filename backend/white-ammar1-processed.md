
---

# List of Figures

| Sr. No. | Name of the Figure | Page No. |
|---------|-------------------|----------|
| 3.1 | Gantt Chart – Project Timeline | |
| 3.2 | Use Case Diagram – PhishGuard AI System | |
| 3.3 | Entity-Relationship Diagram | |
| 3.4 | System Flow Diagram – URL Analysis Pipeline | |
| 3.5 | Class Diagram – Backend Architecture | |
| 3.6 | Sequence Diagram – URL Scan Request | |
| 3.7 | Sequence Diagram – Admin Login and Management | |
| 3.8 | State Diagram – URL Analysis States | |
| 3.9 | State Diagram – User Session States | |
| 3.10 | Menu Tree – Frontend Application | |
| 3.11 | Menu Tree – Admin Panel | |
| 3.12 | Menu Tree – Chrome Extension | |
| 3.13 | Flow Diagram – Heuristic Rule Engine | |
| 3.14 | Flow Diagram – Threat Intelligence Pipeline | |
| 3.15 | Flow Diagram – Brand Impersonation Detection | |

# List of Tables

| Sr. No. | Name of the Table | Page No. |
|---------|------------------|----------|
| 3.1 | Technologies Used – Backend | |
| 3.2 | Technologies Used – Frontend | |
| 3.3 | Technologies Used – Chrome Extension | |
| 3.4 | Technologies Used – Machine Learning | |
| 3.5 | Event Table – System Events | |
| 3.6 | Use Case Description – Scan URL | |
| 3.7 | Use Case Description – View Dashboard | |
| 3.8 | Use Case Description – Admin Login | |
| 3.9 | Use Case Description – Ban User | |
| 3.10 | Use Case Description – Password Audit | |
| 4.1 | scan_results Table Schema | |
| 4.2 | users Table Schema | |
| 4.3 | banned_users Table Schema | |
| 4.4 | Heuristic Rules Summary (16+ Rules) | |
| 4.5 | Trusted Apex Domains Whitelist | |
| 4.6 | Suspicious TLDs List | |
| 4.7 | API Endpoints Summary | |

---

# Chapter 1
# Introduction

> **Chapter Overview:** This chapter introduces PhishGuard AI, a hybrid phishing URL detection system that combines Machine Learning with heuristic rule-based analysis and real-time threat intelligence feeds. The chapter outlines the motivation behind the project, provides a comprehensive description of the system's capabilities, and identifies the key stakeholders who benefit from or interact with the system. The scope and objectives of the project are defined, establishing the foundation for subsequent chapters.

---

## 1.1 Introduction

Phishing is one of the most pervasive and damaging forms of cyberattack in the modern digital landscape. According to the Anti-Phishing Working Group (APWG), the number of phishing attacks reached an all-time high in 2023, with over 4.7 million attacks recorded — a figure that continues to grow year over year [1]. These attacks exploit human trust by creating deceptive websites that impersonate legitimate services such as banking portals, e-commerce platforms, and social media login pages. The ultimate goal is to trick users into divulging sensitive information including passwords, credit card numbers, and personal identification details.

Traditional approaches to combating phishing have relied heavily on blacklist-based detection systems, where known malicious URLs are catalogued and blocked. While effective for previously identified threats, these systems fundamentally fail against zero-day phishing attacks — newly created URLs that have not yet been reported or catalogued. Studies indicate that the average lifespan of a phishing website is less than 24 hours [2], meaning that by the time a URL is blacklisted, the damage has often already been done.

The motivation behind **PhishGuard AI** stems from the critical need for a proactive, intelligent, and multi-layered approach to phishing detection. Rather than relying on a single detection methodology, PhishGuard AI implements a **hybrid detection engine** that synergizes three distinct analytical layers:

1. **Machine Learning (ML) Classification:** A Random Forest classifier trained on the PhiUSIIL Phishing URL Dataset, capable of detecting statistical patterns in URL structure that correlate with phishing behavior.

2. **Heuristic Rule Engine:** A comprehensive rule-based system comprising 16+ individually crafted detection rules that analyze URL characteristics such as domain impersonation, suspicious TLDs, IP-based hostnames, URL obfuscation techniques, and brand typosquatting.

3. **Real-Time Threat Intelligence:** Integration with live threat feeds including PhishTank, OpenPhish, and domain similarity analysis, providing up-to-the-minute threat data from the global cybersecurity community.

The system is delivered through three integrated interfaces: a **React-based web dashboard** for detailed URL analysis, a **Chrome browser extension** for real-time passive protection during web browsing, and an **administrative Security Operations Center (SOC) panel** for system monitoring and user management.

### Motivation

The primary motivations for developing PhishGuard AI are:

- **Inadequacy of Single-Method Detection:** No single technique — whether ML, heuristics, or blacklists — provides sufficient coverage against the full spectrum of phishing techniques. A hybrid approach dramatically reduces false negatives and false positives.
- **Need for Real-Time Protection:** Users need protection at the moment they encounter a potentially malicious URL, not hours after it has been reported. Browser-integrated detection provides this immediacy.
- **Explainability Gap:** Most existing tools provide a binary "safe/unsafe" verdict without explaining *why* a URL was flagged. PhishGuard AI includes an Explainable AI chat system that generates detailed, human-readable threat analysis reports.
- **Accessibility:** Enterprise-grade phishing detection tools are often expensive and complex. PhishGuard AI provides a free, open-source solution that can be deployed locally.

### Scope of the Project

The scope of PhishGuard AI encompasses:

- Training and deploying a Random Forest ML model for URL classification
- Implementing a 16+ rule heuristic analysis engine
- Integrating PhishTank and OpenPhish threat intelligence feeds
- Building a responsive React + TypeScript web frontend
- Developing a Chrome extension for passive real-time scanning
- Creating an admin SOC dashboard for monitoring and user management
- Implementing an Explainable AI endpoint for generating threat reports
- Providing password strength auditing as an auxiliary security tool
- Domain intelligence (WHOIS-style) lookups
- SQLite-based persistent logging and analytics

### Objectives

The key objectives of this project are:

1. To design and implement a hybrid phishing detection system achieving high accuracy with minimal false positives
2. To provide real-time browser-level protection through a Chrome extension
3. To create an intuitive, modern user interface for threat analysis
4. To integrate multiple open-source threat intelligence feeds
5. To implement explainable AI for transparent threat reporting
6. To provide administrative tools for system monitoring and user management

---

## 1.2 Description

**PhishGuard AI** is a full-stack, hybrid phishing URL detection platform built to identify and classify potentially malicious URLs in real-time. The system architecture follows a client-server model with a Python Flask backend serving as the detection engine and API layer, a React TypeScript frontend providing the user interface, and a Chrome Manifest V3 extension enabling passive browser protection.

### System Architecture Overview

The system is composed of four major components:

**1. Backend Detection Engine (Python/Flask)**

The core of PhishGuard AI resides in the Flask backend (app.py), which exposes RESTful API endpoints for URL analysis. When a URL is submitted for scanning, it passes through a multi-stage analysis pipeline:

- **URL Normalization:** The raw URL is sanitized, decoded (URL-encoded characters), and standardized (scheme lowercased, hostname lowercased, default ports stripped).
- **URL Validation:** The normalized URL is validated against regex patterns to ensure it is a well-formed HTTP/HTTPS URL.
- **Feature Extraction:** Six numerical features are extracted from the URL structure — URLLength, DomainLength, IsDomainIP, TLDLength, NoOfSubDomain, and IsHTTPS.
- **ML Inference:** The extracted features are passed to a pre-trained Random Forest model which outputs a phishing probability score.
- **Heuristic Analysis:** The URL is evaluated against 16+ heuristic rules, each contributing a weighted score.
- **Threat Intelligence Checks:** The URL is checked against PhishTank database, OpenPhish feed, domain similarity analysis, redirect chain analysis, and URL shortener detection.
- **Score Fusion:** The ML score, heuristic score, and threat intelligence score are combined using a weighted formula: `0.50 × ML + 0.30 × Heuristic + 0.20 × Threat Intel`.
- **Classification:** The fused score is classified into risk levels (SAFE, SUSPICIOUS, PHISHING) with sub-levels (safe, low, medium, high, critical).

**2. Web Frontend (React + TypeScript + Vite)**

The frontend is a single-page application built with React 19, TypeScript, and Vite. It features a dark-themed, cybersecurity-inspired UI with glass-morphism design elements. The frontend consists of four main pages:

- **Dashboard:** Real-time threat statistics, scan history, API health status
- **URL Scanner:** Primary analysis interface with ML scores, heuristic flags, threat intelligence results, WHOIS lookup, and AI-generated explanations
- **Password Auditor:** Password strength analysis with scoring, improvement suggestions, and secure password generation
- **About:** Project information, technology stack, and disclaimer

**3. Chrome Browser Extension (Manifest V3)**

The Chrome extension operates as a passive security layer that automatically scans every webpage the user visits. It uses a background service worker that listens for tab update events and sends the URL to the Flask backend for analysis. Results are cached in Chrome's local storage and displayed in a popup interface showing risk score, verdict, ML score, rule score, and detection flags.

**4. Admin SOC Dashboard**

A separate administrative interface provides Security Operations Center functionality including:
- Real-time system statistics (total scans, phishing detections, safe URLs, active users)
- 7-day detection trend charts
- Recent scan results table
- User management (view active users, ban/unban users)
- Banned users list
- Threat intelligence feed status monitoring

### Key Features Summary

| Feature | Description |
|---------|-------------|
| Hybrid ML + Heuristic Detection | Random Forest ML model combined with 16+ heuristic rules |
| Real-Time Threat Intelligence | PhishTank database, OpenPhish feed integration |
| Brand Impersonation Detection | Levenshtein distance + leet-speak normalization for typosquatting |
| Domain Spoofing Analysis | Subdomain abuse and trusted brand embedding detection |
| URL Shortener Expansion | Detection and expansion of shortened URLs (bit.ly, tinyurl, etc.) |
| Redirect Chain Analysis | Multi-hop redirect detection with risk scoring |
| Explainable AI | Natural language threat explanations via /chat endpoint |
| Chrome Extension | Passive real-time protection with auto-scanning |
| Password Auditor | Strength scoring, common password detection, secure generation |
| Admin SOC Dashboard | System monitoring, user management, analytics |
| WHOIS/DNS Lookup | Domain resolution and trust verification |
| Trusted Domain Whitelist | 50+ verified apex domains to reduce false positives |
| In-Memory TTL Cache | Thread-safe caching to reduce network overhead |
| SQLite Logging | Persistent scan history, user tracking, ban management |

---

## 1.3 Stakeholders

The stakeholders of PhishGuard AI encompass all individuals and groups who interact with, benefit from, or are affected by the system. They are categorized as follows:

### Primary Stakeholders

| Stakeholder | Role | Interest |
|-------------|------|----------|
| End Users (General Public) | Use the web scanner and Chrome extension to check URLs | Protection from phishing attacks; clear, understandable threat reports |
| System Administrators | Deploy, configure, and maintain the PhishGuard AI backend | System stability, accurate detection, low false positive rate |
| SOC Analysts (Admin Panel Users) | Monitor system health, manage users, review scan logs | Real-time visibility into threat landscape, user management capabilities |

### Secondary Stakeholders

| Stakeholder | Role | Interest |
|-------------|------|----------|
| Cybersecurity Researchers | Study phishing detection methodologies | Access to detection algorithms, heuristic rule documentation, ML model performance |
| Web Browser Vendors | Browsers where the extension operates | Extension compliance with Manifest V3 security standards |
| Threat Intelligence Providers | PhishTank, OpenPhish | Their feeds are consumed; accuracy and uptime of feed data |
| Educational Institutions | Use as teaching/research tool | Understanding of hybrid ML approaches, practical cybersecurity tool |
| Organizations / Enterprises | Deploy for employee protection | Reduced phishing incident rate, centralized monitoring via admin panel |

### Stakeholder Interaction Diagram

![Diagram 1](diagrams/diagram-1773800811251-1.png)

### Summary

Chapter 1 introduced PhishGuard AI as a hybrid phishing detection platform that addresses the critical limitations of single-method detection approaches. The system combines Machine Learning, heuristic rules, and threat intelligence feeds to provide comprehensive URL analysis. The project scope, objectives, and stakeholder ecosystem were defined. In the next chapter, we present a detailed literature survey examining existing phishing detection systems and their limitations, establishing the academic foundation for PhishGuard AI's design decisions.

---

# Chapter 2
# Literature Survey

> **Chapter Overview:** This chapter presents a comprehensive review of existing literature on phishing detection systems, URL classification techniques, and threat intelligence methodologies. Existing systems are examined across three categories — blacklist-based, machine learning-based, and heuristic-based approaches. The limitations of each approach are analyzed, establishing the justification for PhishGuard AI's hybrid architecture. The chapter concludes with a summary of identified research gaps and the objectives derived from the literature survey.

---

## 2.1 Description of Existing Systems

Phishing detection has been extensively studied in cybersecurity research. Existing systems can be broadly categorized into four approaches: blacklist-based, machine learning-based, heuristic-based, and hybrid approaches. This section surveys representative systems from each category.

### 2.1.1 Blacklist-Based Systems

Blacklist-based detection is the earliest and most widely deployed approach to phishing prevention. Systems like **Google Safe Browsing** [3] and **Microsoft SmartScreen** [4] maintain centralized databases of known malicious URLs. When a user navigates to a website, the browser checks the URL against the blacklist and displays a warning if a match is found.

**Google Safe Browsing** protects over 4 billion devices daily and is integrated into Chrome, Firefox, and Safari. It maintains a database updated every 30 minutes through a combination of automated web crawling and user reports. SmartScreen, integrated into Microsoft Edge and Windows, uses a similar approach augmented by URL reputation scoring based on download history and certificate analysis.

**PhishTank** [5] is a collaborative anti-phishing platform operated by Cisco's OpenDNS. It allows users to submit, verify, and track phishing URLs through a community-driven process. The platform provides both an API for real-time lookups and downloadable CSV datasets. As of 2024, the PhishTank database contains over 100,000 verified phishing URLs, with thousands of new entries added daily.

**OpenPhish** [6] is an automated phishing intelligence platform that uses proprietary algorithms to detect phishing sites without human intervention. It provides a free community feed of active phishing URLs updated multiple times daily, as well as premium feeds with enriched data including targeted brands, hosting details, and confidence scores.

### 2.1.2 Machine Learning-Based Systems

Machine learning approaches treat phishing detection as a binary classification problem, extracting features from URLs, page content, or network behavior and training classifiers to distinguish phishing from legitimate sites.

**Sahingoz et al. (2019)** [7] proposed a real-time phishing detection system using seven different classification algorithms (Random Forest, Decision Tree, Naive Bayes, K-Nearest Neighbors, Logistic Regression, SVM, and Adaboost) on a dataset of 73,575 URLs. Their study found that Random Forest achieved the highest accuracy of 97.98% using NLP-based features extracted from URLs. The features included word-level analysis, character-level analysis, and structural features of the URL string.

**Rao and Pais (2019)** [8] developed PhishShield, a URL-based phishing detection system using lexical features. They extracted 30 features from URLs including length of hostname, path, top-level domain, number of dots, special characters, and entropy measurements. Using a Random Forest classifier, they achieved 96.28% accuracy on a balanced dataset of 30,000 URLs.

**Mohammad et al. (2014)** [9] conducted an influential study on intelligent phishing detection using a neuro-fuzzy framework. They identified 17 features spanning URL-based, domain-based, and page-based categories. Their neural network approach achieved 98.5% accuracy, establishing that URL-based features alone can provide strong discriminatory power.

**Jain and Gupta (2018)** [10] proposed a machine learning approach using URL features for client-side phishing detection. They used 19 features and compared the performance of 7 classifiers, concluding that Random Forest provided the best balance of accuracy (99.09%) and computational efficiency for real-time deployment scenarios.

### 2.1.3 Heuristic-Based Systems

Heuristic approaches use manually crafted rules based on known phishing patterns and characteristics.

**Zhang et al. (2007)** [11] developed CANTINA, a content-based approach that uses Term Frequency-Inverse Document Frequency (TF-IDF) to extract key terms from web pages and compare them against search engine results. If the legitimate site does not appear in the top search results for the page's key terms, the page is flagged as potential phishing.

**Garera et al. (2007)** [12] proposed a heuristic classification approach using URL-based features. They identified four types of heuristic features: presence of IP-based URLs, use of obfuscation techniques (such as hexadecimal encoding and the "@" redirect trick), domain-level features (presence of known brand names in non-authoritative domains), and page-level features.

**Typosquatting Detection** is a specialized heuristic technique studied extensively by **Nikiforakis et al. (2014)** [13]. Their work analyzed how attackers create domain names that are visually similar to legitimate brands through character substitution, addition, deletion, or transposition. Detection methods include calculating edit distance (Levenshtein distance) between candidate domains and known brand names, as well as applying leet-speak normalization tables (e.g., "0" → "o", "1" → "l", "3" → "e").

### 2.1.4 Hybrid Systems

Some researchers have explored combining multiple detection techniques.

**Xiang et al. (2011)** [14] developed CANTINA+, which combines URL-based heuristics, page content analysis, and search engine-based verification in a hybrid framework. Their system achieved a 92% true positive rate with a 1.4% false positive rate on a dataset of 7,545 URLs.

**Marchal et al. (2017)** [15] proposed PhishStorm, which performs real-time phishing detection by analyzing the intra-URL relatedness of words in URLs. By combining NLP-based URL analysis with external verification queries, their hybrid system achieved 94.91% accuracy.

**Wei et al. (2020)** [16] proposed a deep learning-based hybrid approach that combines CNN-based URL analysis with WHOIS-based domain intelligence. Their system achieves 98.7% accuracy by leveraging both textual patterns in URLs and domain registration metadata.

### Comparative Analysis of Existing Systems

| System | Approach | Features Used | Accuracy | Real-Time | Explainable |
|--------|----------|---------------|----------|-----------|-------------|
| Google Safe Browsing [3] | Blacklist | URL matching | N/A (blacklist) | Yes | No |
| PhishTank [5] | Crowdsourced Blacklist | URL matching | N/A (blacklist) | Yes (API) | No |
| Sahingoz et al. [7] | ML (Random Forest) | NLP URL features | 97.98% | No | No |
| PhishShield [8] | ML (Random Forest) | 30 lexical features | 96.28% | Yes | No |
| Mohammad et al. [9] | ML (Neural Network) | 17 features | 98.50% | No | No |
| Jain and Gupta [10] | ML (Random Forest) | 19 URL features | 99.09% | Yes | No |
| CANTINA [11] | Heuristic + Content | TF-IDF terms | 89.00% | No | Partial |
| Garera et al. [12] | Heuristic | 4 URL features | 95.80% | Yes | No |
| CANTINA+ [14] | Hybrid (Heuristic + ML) | URL + Content + SE | 92.00% | Partial | No |
| PhishStorm [15] | Hybrid (NLP + External) | Intra-URL words | 94.91% | Yes | No |
| **PhishGuard AI (Ours)** | **Hybrid (ML + Heuristic + Intel)** | **6 ML + 16+ rules + feeds** | **~97%** | **Yes** | **Yes** |

---

## 2.2 Limitations of Present Systems

Based on the literature survey conducted, the following critical limitations were identified across existing phishing detection systems:

### Limitation 1: Single-Method Vulnerability

Most existing systems rely on a single detection methodology. Blacklist-based systems cannot detect zero-day phishing URLs. ML-based systems can be evaded through adversarial URL crafting. Heuristic systems miss attacks that don't match predefined rules. No single method provides comprehensive coverage.

### Limitation 2: Lack of Explainability

The vast majority of existing systems provide binary verdicts (phishing/legitimate) without explaining the reasoning behind the classification. This is a significant limitation for end users who cannot understand why a URL was flagged, and for SOC analysts who need to validate and investigate alerts. None of the surveyed ML-based systems [7-10] provide human-readable explanations.

### Limitation 3: Static Threat Intelligence

Blacklist-based systems suffer from inherent update latency. The APWG reports that the median time from phishing site deployment to blacklist inclusion is 4-8 hours [17]. During this window, users remain unprotected. Systems that do not integrate live threat feeds miss this critical real-time dimension.

### Limitation 4: No Browser-Level Integration

Most academic phishing detection systems exist as standalone tools or server-side systems. They lack direct integration with web browsers, meaning users must actively copy and submit URLs for analysis. This friction dramatically reduces adoption and utility. Only Google Safe Browsing and Microsoft SmartScreen provide browser-level passive protection, but both rely solely on blacklists.

### Limitation 5: Limited Typosquatting Detection

Typosquatting and brand impersonation represent a growing attack vector. While Nikiforakis et al. [13] studied the problem extensively, few production systems implement comprehensive typosquatting detection that combines edit distance calculation with leet-speak normalization and multi-brand coverage.

### Limitation 6: No User Management or Monitoring

Existing open-source phishing detection tools typically lack administrative interfaces for monitoring system health, managing users, or analyzing detection trends. This limits their usefulness in organizational deployments where SOC analysts need visibility into the threat landscape.

### Limitation 7: High False Positive Rates on Trusted Domains

Many ML-based systems produce false positives for legitimate URLs from trusted domains like Google, Microsoft, and Amazon. This is because URL features such as length and number of subdomains can be high for legitimate services (e.g., `accounts.google.com/signin/v2/identifier`). Most systems lack a trusted domain whitelist mechanism.

### Summary of Identified Research Gaps

| Gap ID | Description | Impact |
|--------|-------------|--------|
| G1 | No hybrid system combining ML + Heuristics + Live Threat Intel | Incomplete detection coverage |
| G2 | Lack of explainable AI in phishing detection | Users cannot understand or trust verdicts |
| G3 | No passive browser-level real-time protection (beyond blacklists) | Users must actively scan URLs |
| G4 | Insufficient typosquatting/brand impersonation detection | Growing attack vector unaddressed |
| G5 | No SOC/admin monitoring interface in open-source tools | Cannot deploy in organizations |
| G6 | High false positive rate on trusted domains | User trust and usability degraded |
| G7 | No integrated password security auditing | Holistic security approach missing |

### Objectives Derived from Literature Survey

Based on the identified gaps, the following objectives are defined for PhishGuard AI:

1. **O1 (addresses G1):** Design a hybrid detection engine combining Random Forest ML, 16+ heuristic rules, and live PhishTank/OpenPhish threat intelligence feeds
2. **O2 (addresses G2):** Implement an Explainable AI endpoint that generates natural language threat analysis reports
3. **O3 (addresses G3):** Develop a Chrome Manifest V3 extension for passive, real-time URL scanning during web browsing
4. **O4 (addresses G4):** Implement comprehensive brand impersonation detection using Levenshtein distance and leet-speak normalization across 35+ known brands
5. **O5 (addresses G5):** Build an administrative SOC dashboard with real-time statistics, user management, and detection trend analysis
6. **O6 (addresses G6):** Implement a 50+ entry trusted domain whitelist with trust-override logic to minimize false positives
7. **O7 (addresses G7):** Include a password strength auditor with common password detection and secure generation

### Summary

Chapter 2 surveyed existing phishing detection systems across four categories: blacklist-based, machine learning-based, heuristic-based, and hybrid approaches. Seven critical limitations were identified, and corresponding research objectives for PhishGuard AI were defined. The comparative analysis demonstrated that no existing system provides the combination of hybrid ML+heuristic+threat intelligence detection, explainable AI, browser extension integration, and administrative monitoring that PhishGuard AI delivers. In the next chapter, we present the detailed methodology including system architecture, technology stack, and design artifacts.

### References (for Chapter 2)

[1] Anti-Phishing Working Group (APWG), "Phishing Activity Trends Report, Q4 2023," APWG, 2024.

[2] A. Y. Lam, S. Li, and D. Goldsmith, "A Survival Analysis of Phishing Websites," *IEEE International Conference on Intelligence and Security Informatics*, 2009.

[3] Google, "Google Safe Browsing," https://safebrowsing.google.com/, Accessed 2025.

[4] Microsoft, "Microsoft Defender SmartScreen," https://learn.microsoft.com/en-us/windows/security/threat-protection/microsoft-defender-smartscreen/, Accessed 2025.

[5] PhishTank, "PhishTank – Join the fight against phishing," https://www.phishtank.com/, Accessed 2025.

[6] OpenPhish, "OpenPhish – Phishing Intelligence," https://openphish.com/, Accessed 2025.

[7] O. K. Sahingoz, E. Buber, O. Demir, and B. Diri, "Machine Learning Based Phishing Detection from URLs," *Expert Systems with Applications*, vol. 117, pp. 345–357, 2019.

[8] R. S. Rao and A. R. Pais, "PhishShield: A Desktop Application to Detect Phishing Webpages through Heuristic Approach," *Procedia Computer Science*, vol. 54, pp. 147–156, 2019.

[9] R. M. Mohammad, F. Thabtah, and L. McCluskey, "Intelligent Rule-Based Phishing Websites Classification," *IET Information Security*, vol. 8, no. 3, pp. 153–160, 2014.

[10] A. K. Jain and B. B. Gupta, "Towards Detection of Phishing Websites on Client-Side Using Machine Learning Based Approach," *Telecommunication Systems*, vol. 68, no. 4, pp. 687–700, 2018.

[11] Y. Zhang, J. I. Hong, and L. F. Cranor, "CANTINA: A Content-Based Approach to Detecting Phishing Web Sites," *Proceedings of the 16th International Conference on World Wide Web*, pp. 639–648, 2007.

[12] S. Garera, N. Provos, M. Chew, and A. D. Rubin, "A Framework for Detection and Measurement of Phishing Attacks," *Proceedings of the 2007 ACM Workshop on Recurring Malcode*, pp. 1–8, 2007.

[13] N. Nikiforakis, M. Balduzzi, L. Desmet, F. Piessens, and W. Joosen, "Soundsquatting: Uncovering the Use of Homophones in Domain Squatting," *International Conference on Information Security*, pp. 291–308, 2014.

[14] G. Xiang, J. Hong, C. P. Rose, and L. Cranor, "CANTINA+: A Feature-Rich Machine Learning Framework for Detecting Phishing Web Sites," *ACM Transactions on Information and System Security*, vol. 14, no. 2, pp. 1–28, 2011.

[15] S. Marchal, J. François, R. State, and T. Engel, "PhishStorm: Detecting Phishing with Streaming Analytics," *IEEE Transactions on Network and Service Management*, vol. 11, no. 4, pp. 458–471, 2017.

[16] B. Wei, R. A. Hamad, L. Yang, T. He, and A. L. Sherazi, "A Deep-Learning-Driven Light-Weight Phishing Detection Sensor," *Sensors*, vol. 20, no. 21, p. 6258, 2020.

[17] APWG, "Global Phishing Survey: Trends and Domain Name Use," APWG, 2022.

[18] S. Abu-Nimeh, D. Nappa, X. Wang, and S. Nair, "A Comparison of Machine Learning Techniques for Phishing Detection," *Proceedings of the Anti-Phishing Working Group eCrime Researchers Summit*, pp. 60–69, 2007.

[19] R. Verma and K. Dyer, "On the Character of Phishing URLs: Accurate and Robust Statistical Learning Classifiers," *Proceedings of the ACM Conference on Data and Application Security and Privacy*, pp. 111–122, 2015.

[20] J. Ma, L. K. Saul, S. Savage, and G. M. Voelker, "Beyond Blacklists: Learning to Detect Malicious Web Sites from Suspicious URLs," *Proceedings of the ACM SIGKDD International Conference on Knowledge Discovery and Data Mining*, pp. 1245–1254, 2009.

---

# Chapter 3
# Methodology

> **Chapter Overview:** This chapter details the complete methodology employed in the design and development of PhishGuard AI. It covers the project timeline via a Gantt chart, the technology stack, system events, UML design diagrams (Use Case, Entity-Relationship, Flow, Class, Sequence, and State diagrams), and the application menu tree. Each diagram is accompanied by descriptive text explaining the design decisions and system interactions. All diagrams are provided as Mermaid code for reproducibility.

---

## 2.3 Gantt Chart (Timeline)

The PhishGuard AI project was developed over a six-month period following an iterative development methodology. The Gantt chart below illustrates the timeline of major project phases:

**Figure 3.1: Gantt Chart – Project Timeline**

![Diagram 2](diagrams/diagram-1773800815782-2.png)

---

## 3.1 Technologies Used and Their Description

The technologies used in PhishGuard AI span backend development, frontend development, browser extension development, and machine learning. Each technology was selected based on its suitability for the specific requirements of the component.

### Table 3.1: Technologies Used – Backend

| Technology | Version | Purpose | Description |
|------------|---------|---------|-------------|
| Python | 3.11+ | Backend Language | High-level, interpreted language with excellent ML ecosystem and rapid development capabilities |
| Flask | 3.1.0 | Web Framework | Lightweight WSGI micro-framework for building RESTful APIs. Chosen for its simplicity and extensibility |
| Flask-CORS | 5.0.0 | Cross-Origin Support | Enables Cross-Origin Resource Sharing for frontend-backend communication across different ports |
| scikit-learn | 1.6.1 | Machine Learning | Industry-standard ML library providing the RandomForestClassifier implementation |
| pandas | 2.2.3 | Data Processing | DataFrame-based data manipulation library used for feature extraction and model inference |
| joblib | 1.4.2 | Model Serialization | Efficient serialization of trained ML models to disk (.joblib format) |
| requests | 2.32.3 | HTTP Client | HTTP library for fetching threat intelligence feeds (PhishTank, OpenPhish) |
| python-dotenv | 1.0.1 | Environment Config | Loads environment variables from .env files for secure configuration |
| SQLite3 | Built-in | Database | Serverless relational database for scan logging, user tracking, and ban management |

### Table 3.2: Technologies Used – Frontend

| Technology | Version | Purpose | Description |
|------------|---------|---------|-------------|
| React | 19.0.0 | UI Framework | Component-based JavaScript library for building reactive user interfaces |
| TypeScript | 5.7.2 | Type Safety | Typed superset of JavaScript providing compile-time type checking and better IDE support |
| Vite | 6.2.0 | Build Tool | Next-generation frontend build tool with fast HMR (Hot Module Replacement) and optimized builds |
| Tailwind CSS | 4.0.14 | Styling | Utility-first CSS framework enabling rapid UI development with consistent design tokens |
| React Router | 7.12.0 | Routing | Client-side routing library for single-page application navigation |
| Recharts | 2.15.3 | Data Visualization | React-based charting library used for the admin dashboard detection trend charts |
| Lucide React | 0.479.0 | Icons | Modern icon library providing 1000+ SVG icons with React components |
| Radix UI | Latest | Primitives | Headless, accessible UI component primitives (AlertDialog, etc.) |
| clsx + tailwind-merge | Latest | Utility | CSS class merging utilities for conditional styling |

### Table 3.3: Technologies Used – Chrome Extension

| Technology | Version | Purpose | Description |
|------------|---------|---------|-------------|
| Manifest V3 | 3 | Extension Standard | Latest Chrome extension architecture with enhanced security (service workers instead of background pages) |
| Service Workers | - | Background Processing | Event-driven scripts for intercepting tab navigation and triggering URL scans |
| Chrome Storage API | - | Data Persistence | Local storage for caching scan results per browser tab |
| Chrome Tabs API | - | Tab Monitoring | Listening for tab update events (page load completion) to trigger auto-scans |

### Table 3.4: Technologies Used – Machine Learning

| Technology | Purpose | Details |
|------------|---------|---------|
| Random Forest Classifier | URL Classification | Ensemble of 50 decision trees with max depth 10, trained on PhiUSIIL dataset |
| PhiUSIIL Dataset | Training Data | 235,795 URLs (phishing + legitimate) with 50+ features; 6 selected for model |
| Train-Test Split | Evaluation | 80/20 stratified split for unbiased accuracy measurement |
| Feature Set | Input Variables | URLLength, DomainLength, IsDomainIP, TLDLength, NoOfSubDomain, IsHTTPS |
| Accuracy | Performance Metric | ~97% test accuracy on held-out data |

### Technology Architecture Diagram

![Diagram 3](diagrams/diagram-1773800820415-3.png)

---

## 3.2 Event Table

The event table identifies the key events in the PhishGuard AI system, their triggers, sources, responses, and the destinations of those responses.

### Table 3.5: Event Table – System Events

| Event ID | Event Name | Trigger | Source | Activity | Response | Destination |
|----------|-----------|---------|--------|----------|----------|-------------|
| E1 | URL Scan Request | User clicks "Analyze" button | Web Frontend / Chrome Extension | Normalize URL → Extract features → Run ML → Run heuristics → Check threat intel → Fuse scores → Classify | JSON response with risk_score, result, flags, checks | Frontend UI / Extension Popup |
| E2 | AI Explanation Request | Scan completes successfully | Web Frontend (automatic) | Generate natural language explanation based on result, flags, scores | Markdown-formatted threat analysis text | Scanner page explanation panel |
| E3 | WHOIS Lookup | Scan completes successfully | Web Frontend (automatic) | DNS resolution, domain trust check | Domain info, IP addresses, trust status | Scanner page WHOIS panel |
| E4 | Page Navigation | User navigates to new page | Chrome Browser | Extension background worker detects tab update → sends URL to /predict | Cached scan result stored in chrome.storage | Extension popup (on open) |
| E5 | Manual Extension Scan | User clicks "Check This Page" | Extension Popup | Send message to background worker → POST to /predict | Rendered result in popup UI | Extension popup |
| E6 | Admin Login | Admin enters credentials | Admin Login Page | Validate username/password → Create session | Session cookie + success JSON | Admin Dashboard redirect |
| E7 | View System Stats | Admin opens dashboard | Admin Dashboard | Query database for counts | Total scans, phishing count, safe count, active users | Stats cards component |
| E8 | View Recent Scans | Admin opens dashboard | Admin Dashboard | Query scan_results table (last 50) | List of scan records with URL, score, result, time | Recent scans table |
| E9 | Ban User | Admin clicks "Ban" button | Admin Users Table | Insert into banned_users + Update users.status | Success confirmation | Users table refresh |
| E10 | Unban User | Admin clicks "Unban" button | Admin Banned Users | Delete from banned_users + Update users.status | Success confirmation | Banned users table refresh |
| E11 | Password Audit | User types password | Password Page | Evaluate strength rules → Calculate score | Score, label, color, suggestions | Password strength UI |
| E12 | Password Generation | User clicks "Generate" | Password Page | Crypto-secure random character selection | 16-character strong password | Password input field |
| E13 | Health Check | Frontend loads | Dashboard Page | Poll /health endpoint | API status (online/offline) | Status indicator |
| E14 | Feed Refresh | Background timer (hourly) | Backend Thread | Re-download OpenPhish feed + PhishTank CSV | Updated cache entries | In-memory cache |
| E15 | Clear Dashboard Data | User clicks "Clear Data" | Dashboard Page | Remove localStorage items | Reset stats and history | Dashboard UI refresh |
| E16 | Banned User Scan Attempt | Banned user submits URL | Any client | Check banned_users table | HTTP 403 Forbidden with error message | Error display |

---

## 3.3 Use Case Diagram and Basic Scenarios & Use Case Description

### Use Case Diagram

**Figure 3.2: Use Case Diagram – PhishGuard AI System**

![Diagram 4](diagrams/diagram-1773800824736-4.png)

### Use Case Descriptions

**Table 3.6: Use Case Description – Scan URL (UC1)**

| Field | Description |
|-------|-------------|
| **Use Case ID** | UC1 |
| **Use Case Name** | Scan URL |
| **Actor(s)** | End User, Chrome Extension |
| **Description** | User submits a URL for phishing analysis. The system normalizes, validates, and processes the URL through ML model, heuristic engine, and threat intelligence checks, returning a comprehensive risk assessment. |
| **Pre-conditions** | 1. Backend API is running and accessible. 2. ML model file (phish_model.joblib) is loaded. 3. User is not banned. |
| **Post-conditions** | 1. Scan result is displayed to user. 2. Scan is logged in database. 3. User activity is tracked. 4. Result is saved to scan history (localStorage). |
| **Primary Flow** | 1. User enters URL in the scanner input field. 2. User clicks "Analyze" button or presses Enter. 3. System normalizes the URL (adds scheme, decodes, lowercases). 4. System validates URL format. 5. System extracts 6 numerical features. 6. System runs ML model inference (Random Forest). 7. System executes 16+ heuristic rules. 8. System checks PhishTank, OpenPhish, domain similarity, redirects, URL shorteners. 9. System fuses scores: 50% ML + 30% Heuristic + 20% Threat Intel. 10. System classifies risk level (SAFE/SUSPICIOUS/PHISHING). 11. System returns JSON response with all analysis data. 12. Frontend renders result card with scores, flags, and risk visualization. |
| **Alternate Flow** | A1. URL is empty → System returns "No URL provided" error. A2. URL format invalid → System returns validation error. A3. User is banned → System returns HTTP 403 "User is banned". A4. ML model fails → System uses fallback score of 0.5. |
| **Exception Flow** | E1. Backend unreachable → Frontend shows "Connection Error" message. E2. Threat intel feeds unavailable → System continues with ML + heuristic only. |

**Table 3.7: Use Case Description – View Dashboard (UC4)**

| Field | Description |
|-------|-------------|
| **Use Case ID** | UC4 |
| **Use Case Name** | View Dashboard Statistics |
| **Actor(s)** | End User |
| **Description** | User views the main dashboard showing aggregate scan statistics, recent scan history, and backend health status. |
| **Pre-conditions** | User has the frontend loaded in browser. |
| **Post-conditions** | Dashboard displays current statistics from localStorage. |
| **Primary Flow** | 1. User navigates to "/" route. 2. System loads stats from localStorage (totalScanned, phishingCount, lastUrl). 3. System loads scan history from localStorage. 4. System calls /health endpoint to check API status. 5. Dashboard renders stat cards, threat analysis chart, and activity log. |
| **Alternate Flow** | A1. No previous scans → Dashboard shows "No scans yet" message. A2. API offline → Status shows "API Offline" indicator. |

**Table 3.8: Use Case Description – Admin Login (UC10)**

| Field | Description |
|-------|-------------|
| **Use Case ID** | UC10 |
| **Use Case Name** | Admin Login |
| **Actor(s)** | Administrator / SOC Analyst |
| **Description** | Admin authenticates using credentials to access the SOC dashboard. |
| **Pre-conditions** | Admin has valid credentials. Backend is running. |
| **Post-conditions** | Admin session is created. Admin is redirected to SOC dashboard. |
| **Primary Flow** | 1. Admin navigates to /admin route. 2. System displays login form. 3. Admin enters username and password. 4. System validates credentials against stored values. 5. System creates server-side session (admin_logged_in). 6. System returns success response. 7. Frontend redirects to /admin/dashboard. |
| **Alternate Flow** | A1. Invalid credentials → System returns HTTP 401 "Invalid credentials". |

**Table 3.9: Use Case Description – Ban User (UC14)**

| Field | Description |
|-------|-------------|
| **Use Case ID** | UC14 |
| **Use Case Name** | Ban User |
| **Actor(s)** | Administrator |
| **Description** | Admin bans a user, preventing them from using the scan service. |
| **Pre-conditions** | Admin is logged in. Target user exists in the system. |
| **Post-conditions** | User is added to banned_users table. User status updated to 'banned'. Subsequent scan requests from this user return HTTP 403. |
| **Primary Flow** | 1. Admin views user list in SOC dashboard. 2. Admin clicks "Ban" button next to target user. 3. Confirmation dialog appears. 4. Admin confirms ban action. 5. System inserts record into banned_users table. 6. System updates user status to 'banned' in users table. 7. System returns success confirmation. 8. User list refreshes to reflect new status. |

**Table 3.10: Use Case Description – Password Audit (UC6)**

| Field | Description |
|-------|-------------|
| **Use Case ID** | UC6 |
| **Use Case Name** | Audit Password Strength |
| **Actor(s)** | End User |
| **Description** | User enters a password to evaluate its strength against multiple criteria. |
| **Pre-conditions** | User is on the Password page. |
| **Post-conditions** | Strength score, label, and improvement suggestions are displayed. |
| **Primary Flow** | 1. User navigates to /password route. 2. User types a password into the input field. 3. System evaluates in real-time: length bonus, character diversity, common password check, pattern detection. 4. System calculates score (0-100), assigns label and color. 5. System generates list of improvement suggestions. 6. UI renders strength meter, score, label, and suggestions. |

---

## 3.4 Entity-Relationship Diagram

The PhishGuard AI database uses SQLite with three main tables: `scan_results`, `users`, and `banned_users`. The ER diagram below shows the relationships between these entities.

**Figure 3.3: Entity-Relationship Diagram**

![Diagram 5](diagrams/diagram-1773800830920-5.png)

### Entity Descriptions

**USERS Entity:** Represents every unique user who has interacted with the system. The `user_id` is generated from the request's identifier (format: `user_{ip_address}`). The `request_count` tracks total API calls for rate monitoring. The `status` field toggles between 'active' and 'banned'.

**SCAN_RESULTS Entity:** Records every URL scan performed. Each record captures the URL, risk score, classification result, timestamp, source (extension/web), and the user who initiated the scan. This table is indexed on `scan_time DESC` for efficient retrieval of recent scans, and on `user_id` for per-user history queries.

**BANNED_USERS Entity:** Contains records of banned users. When an admin bans a user, a record is inserted here with the user's ID, IP address, ban timestamp, and reason. The `/predict` endpoint checks this table before processing any scan request.

---

## 3.5 Flow Diagram

### Flow Diagram 1: URL Analysis Pipeline

**Figure 3.4: System Flow Diagram – URL Analysis Pipeline**

![Diagram 6](diagrams/diagram-1773800835411-6.png)

### Flow Diagram 2: Heuristic Rule Engine

**Figure 3.13: Flow Diagram – Heuristic Rule Engine**

![Diagram 7](diagrams/diagram-1773800840697-7.png)

### Flow Diagram 3: Threat Intelligence Pipeline

**Figure 3.14: Flow Diagram – Threat Intelligence Pipeline**

![Diagram 8](diagrams/diagram-1773800847331-8.png)

### Flow Diagram 4: Brand Impersonation Detection

**Figure 3.15: Flow Diagram – Brand Impersonation Detection**

![Diagram 9](diagrams/diagram-1773800851878-9.png)

---

## 3.6 Class Diagram

**Figure 3.5: Class Diagram – Backend Architecture**

![Diagram 10](diagrams/diagram-1773800858177-10.png)

---

## 3.7 Sequence Diagram

### Sequence Diagram 1: URL Scan Request

**Figure 3.6: Sequence Diagram – URL Scan Request**

![Diagram 11](diagrams/diagram-1773800864811-11.png)

### Sequence Diagram 2: Admin Login and Management

**Figure 3.7: Sequence Diagram – Admin Login and Management**

![Diagram 12](diagrams/diagram-1773800871352-12.png)

### Sequence Diagram 3: Chrome Extension Auto-Scan

![Diagram 13](diagrams/diagram-1773800877273-13.png)

---

## 3.8 State Diagram

### State Diagram 1: URL Analysis States

**Figure 3.8: State Diagram – URL Analysis States**

![Diagram 14](diagrams/diagram-1773800883525-14.png)

### State Diagram 2: User Session States

**Figure 3.9: State Diagram – User Session States**

![Diagram 15](diagrams/diagram-1773800890726-15.png)

### State Diagram 3: Admin Session States

![Diagram 16](diagrams/diagram-1773800895211-16.png)

---

## 3.9 Menu Tree

### Menu Tree 1: Frontend Application

**Figure 3.10: Menu Tree – Frontend Application**

```mermaid
graph TD
    ROOT[PhishGuard AI<br/>Web Application] --> HOME[/ Dashboard<br/>Main landing page]
    ROOT --> SCANNER[/scanner URL Scanner<br/>Primary analysis tool]
    ROOT --> PASSWORD[/password Password Auditor<br/>Strength checker]
    ROOT --> ABOUT[/about About<br/>Project information]

    HOME --> H1[Stat Cards<br/>Total Scans / Threats / Safe / Rate]
    HOME --> H2[Threat Analysis Chart<br/>Safe vs Phishing bar]
    HOME --> H3[Last Scanned URL]
    HOME --> H4[Activity Log<br/>Recent scan history]
    HOME --> H5[API Status Indicator<br/>Online / Offline]
    HOME --> H6[Clear Data Button]

    SCANNER --> S1[URL Input Field]
    SCANNER --> S2[Analyze Button]
    SCANNER --> S3[Result Card]
    S3 --> S3A[Verdict Badge<br/>THREAT DETECTED / LOOKS LEGITIMATE]
    S3 --> S3B[Risk Level Indicator<br/>safe / low / medium / high / critical]
    S3 --> S3C[Risk Score Meter<br/>Visual progress bar]
    S3 --> S3D[Score Breakdown Grid<br/>ML Score / Rules / Combined / Flags]
    S3 --> S3E[Detection Flags List]
    SCANNER --> S4[AI Explanation Panel<br/>Generated threat analysis]
    SCANNER --> S5[WHOIS / Domain Intel Panel<br/>Collapsible section]
    S5 --> S5A[Domain Name]
    S5 --> S5B[IP Addresses]
    S5 --> S5C[Trust Status]
    S5 --> S5D[Lookup Timestamp]

    PASSWORD --> P1[Password Input Field<br/>With show/hide toggle]
    PASSWORD --> P2[Strength Meter Bar]
    PASSWORD --> P3[Score Display & Label]
    PASSWORD --> P4[Criteria Checklist<br/>Length / Upper / Lower / Digit / Special]
    PASSWORD --> P5[Improvement Suggestions]
    PASSWORD --> P6[Generate Password Button]
    PASSWORD --> P7[Copy to Clipboard Button]

    ABOUT --> A1[Project Overview]
    ABOUT --> A2[Technology Stack]
    ABOUT --> A3[Disclaimer]
```

### Menu Tree 2: Admin Panel

**Figure 3.11: Menu Tree – Admin Panel**

```mermaid
graph TD
    ADMIN[Admin Panel] --> LOGIN[/admin Login Page]
    ADMIN --> DASH[/admin/dashboard SOC Dashboard]

    LOGIN --> L1[Username Input]
    LOGIN --> L2[Password Input]
    LOGIN --> L3[Login Button]
    LOGIN --> L4[Error Message Display]

    DASH --> D1[Header Bar<br/>PhishGuard SOC + Logout]
    DASH --> D2[Stats Cards Row]
    D2 --> D2A[Total Scans]
    D2 --> D2B[Phishing Detected]
    D2 --> D2C[Safe URLs]
    D2 --> D2D[Active Users]

    DASH --> D3[Detection Chart<br/>7-day trend Recharts]
    D3 --> D3A[Phishing Line]
    D3 --> D3B[Safe Line]

    DASH --> D4[Threat Intel Status]
    D4 --> D4A[PhishTank Feed Status]
    D4 --> D4B[OpenPhish Feed Status]
    D4 --> D4C[Safe Browsing Status]
    D4 --> D4D[ML Model Status]

    DASH --> D5[Recent Scans Table]
    D5 --> D5A[URL Column]
    D5 --> D5B[Risk Score Column]
    D5 --> D5C[Result Column]
    D5 --> D5D[Time Column]
    D5 --> D5E[Source Column]

    DASH --> D6[Active Users Table]
    D6 --> D6A[User ID Column]
    D6 --> D6B[IP Address Column]
    D6 --> D6C[Request Count Column]
    D6 --> D6D[Status Column]
    D6 --> D6E[Last Seen Column]
    D6 --> D6F[Ban Button + Confirm Dialog]

    DASH --> D7[Banned Users Table]
    D7 --> D7A[User ID Column]
    D7 --> D7B[IP Address Column]
    D7 --> D7C[Ban Time Column]
    D7 --> D7D[Reason Column]
    D7 --> D7E[Unban Button]
```

### Menu Tree 3: Chrome Extension

**Figure 3.12: Menu Tree – Chrome Extension**

![Diagram 19](diagrams/diagram-1773800908883-19.png)

---

### Summary

Chapter 3 presented the complete methodology of the PhishGuard AI system. The project timeline was illustrated through a Gantt chart spanning October 2025 to March 2026. The technology stack was documented across four categories (Backend, Frontend, Chrome Extension, and Machine Learning) with 25+ technologies. The event table catalogued 16 system events with their triggers, activities, and responses. Comprehensive UML design artifacts were provided: a Use Case diagram with 19 use cases and 5 detailed use case descriptions, an Entity-Relationship diagram with 3 database tables, 4 Flow diagrams (URL analysis pipeline, heuristic engine, threat intelligence pipeline, and brand impersonation detection), a Class diagram with 12 classes, 3 Sequence diagrams (URL scan, admin management, and Chrome extension auto-scan), 3 State diagrams (URL analysis, user session, and admin session states), and 3 Menu trees (frontend, admin panel, and Chrome extension). In the next chapter, we present the implementation details including database schema, system coding with annotated code snippets, and screen layouts.

---
