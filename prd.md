# prd.md: Product Requirements

> **Status:** Draft v1. Ye document sirf us context par based hai jo owner ne diya hai. Koi bhi detail jo confirm nahi hui, wo "Open Questions" me hai.
> **Repository status:** Is document likhte waqt koi repository accessible nahi thi. **Kuch bhi implemented nahi maana gaya hai.** Task T-001 repository inspect karke ye confirm karega.

---

## 1. Overview

**Product (working description):** Ek web application jo North India ke crop-residue (stubble) burning season me satellite se detect hui fires dikhata hai, wind data se estimate karta hai ki smoke kis city ki taraf ja sakta hai, subscribed logon ko email alert bhejta hai, aur officers/farmers ke liye structured information deta hai.

**Product name:** Abhi decide nahi hua (Q-01). Code me ek hi config constant `PRODUCT_NAME` rakho, taaki naam baad me ek jagah se badle.

## 2. Problem aur Users

**Problem:** Parali jalne ka dhuan har saal kai shehron ki hawa bigaadta hai. Fire detection data public hai, par use "mere shehar par kab asar padega" aur "kya action lena hai" me convert karne wala simple tool kam milta hai.

**Intended users:**

| User | Kya chahiye |
|------|-------------|
| Residents, schools, communities (NCR aur aas-paas ke shehar) | Smoke aane se pehle estimated warning, current area ka AQI context |
| District / state officials | District-wise fire summary jo print/PDF ho sake |
| Farmers aur farm advisers | Alternatives ki verified jaankari (Hindi + English) |

## 3. Core Features

| ID | Feature | Behaviour |
|----|---------|-----------|
| F1 | Fire Map | Satellite fire detections ke clusters map par, real data se. Top par live stats (computed) |
| F2 | Smoke Impact + Alerts | Wind se estimated smoke direction, cities-at-risk list (distance, ETA, severity), email alert subscription |
| F3 | Advisory + Officer Report | Cluster ke liye verified advisory; district-wise report with print |
| F4 | Archive | Kisi purani date ka data dekhna (same views) |
| F5 | Method aur Data Sources page | Data kahan se aata hai, estimate kaise bana, limitations |
| F6 | Legal pages | Terms of Service, Privacy Policy (draft, review ke liye marked) |

## 4. Functional Requirements

- **FR-01** System NASA FIRMS (VIIRS) se configured region ki fire detections periodically fetch kare (initial: har 30 min, configurable).
- **FR-02** `confidence = low` wali detections hata di jayein. Rule documented ho.
- **FR-03** Detections sirf configured source region ke andar rakhi jayein (boundary polygon se). Sirf bounding box kaafi nahi hai, kyunki wo neighbouring regions ko bhi cover kar leta hai (Q-04).
- **FR-04** Detections ko grid par cluster kiya jaye (count, total FRP, max FRP, centroid, first/last seen).
- **FR-05** Wind data (speed, direction) coarse grid par fetch ho. Direction ka average **circular mean** se nikle, simple arithmetic average se nahi.
- **FR-06** Smoke direction = `(wind_direction + 180) % 360`. Har cluster ke liye configured cities ka impact estimate nikle (distance, bearing, ETA, severity).
- **FR-07** Map par har cluster ka detail (district, last seen IST, FRP, wind) dikhe. Stats bar API ke data se calculate ho, hardcode nahi.
- **FR-08** Cities-at-risk panel: city, ETA, severity, baseline AQI (Open-Meteo air quality, "modelled estimate" label ke saath).
- **FR-09** Email subscription: user email + city deta hai, **double opt-in** (confirmation email) hota hai, har alert me unsubscribe link ho.
- **FR-10** High-severity impact par alert bheja jaye, **cooldown** ke saath (same city ko bar-bar nahi, initial 12 ghante, configurable).
- **FR-11** Advisory content **human-verified static content** ho, har item me source URL aur "last verified" date. LLM-generated advisory v1 me nahi.
- **FR-12** Officer report: date ke hisaab se district-wise table, browser print se PDF ban sake.
- **FR-13** Archive: date picker se purane din ka data (historical FIRMS + historical wind).
- **FR-14** Har data view me loading, error aur empty state ho.
- **FR-15** UI English aur Hindi dono me (language toggle).
- **FR-16** Footer me Terms aur Privacy links, aur data attributions (NASA FIRMS, Open-Meteo, OpenStreetMap).

## 5. Non-Functional Requirements

| Area | Requirement |
|------|-------------|
| Accessibility | WCAG 2.1 AA, keyboard-navigable, visible focus, contrast checked |
| Responsive | 360px width se desktop tak, horizontal overflow nahi |
| Performance | Map first meaningful view ke liye targets T-072 me measure karke agents.md me record hon (abhi numeric target invent nahi kiya) |
| Reliability | Ingest failure par CloudWatch alarm; API failure par UI me clear error |
| Cost | AWS free tier/credits ke andar; Budget alert set; serverless on-demand services |
| Browser support | Modern evergreen browsers (Chrome, Edge, Firefox, Safari latest 2 versions) |
| Maintainability | Backend aur frontend dono me lint + typecheck + tests; config values code me hardcode nahi |

## 6. Technical Constraints aur Dependencies

- **Must be deployed on AWS.** Details `docs/architecture.md` me (Amplify Hosting, API Gateway, Lambda, DynamoDB, EventBridge, SNS, SSM Parameter Store, CloudWatch, SAM).
- External data: NASA FIRMS, Open-Meteo (forecast, historical, air quality), Nominatim (reverse geocode), OpenStreetMap tiles, admin boundary data.
- Ye sab third-party services hain. Unki usage policies/limits ka pata T-004 me official docs se confirm hoga.
- Koi coding owner nahi karega. Saara code Antigravity likhega.

## 7. Security, Privacy, Accessibility

**Security**
- Koi secret frontend bundle, logs ya git me nahi.
- FIRMS key AWS SSM Parameter Store (SecureString) me.
- API par CORS sirf apne frontend domain ke liye, throttling on.
- Subscribe endpoint abuse (kisi aur ke email par spam confirmations) ke against protected: input validation, rate limit, double opt-in.
- Lambda IAM least-privilege.

**Privacy**
- Sirf email + city collect hota hai, aur wo SNS me rehta hai. Koi user accounts nahi.
- Analytics v1 me nahi (Q-09). Fonts self-hosted, taaki visitors ka data font providers ko na jaye.
- Privacy Policy actual data practices se likhi jaye aur "draft" mark ho.

**Accessibility**
- Severity sirf color se nahi, text label se bhi.
- Map ke liye text alternative: cities-at-risk list aur cluster table keyboard se accessible.
- `prefers-reduced-motion` respect ho.

## 8. User Journeys

1. **Resident:** site kholta hai -> apni city dhundta hai -> ETA aur severity dekhta hai -> email subscribe karta hai -> confirmation email click -> baad me alert aata hai.
2. **Officer:** Report page -> date choose -> district table -> Print/Save as PDF.
3. **Farmer / adviser:** map par cluster click -> advisory (Hindi/English) -> source link.
4. **Researcher / curious user:** Method page padhta hai, archive me purani date dekhta hai.

## 9. Success aur Acceptance Criteria

- Ingest Lambda deployed AWS par chalta hai aur DynamoDB me real FIRMS data se clusters likhta hai (CloudWatch log + table items se verified).
- Impact engine ke unit tests known geometry cases par pass (including circular mean wrap-around, e.g. 350 degree aur 10 degree).
- Frontend deployed Amplify par, deployed API se real data dikhata hai.
- Subscribe -> confirm -> alert ka end-to-end test owner ke apne email par kam se kam ek baar successful.
- Lint + typecheck + full tests pass; axe automated check ke results recorded, remaining issues listed.
- `design.md` ke restrictions ka final review done.
- Koi hardcoded/mock data product me nahi (test fixtures ke alawa, jo clearly labelled hain).

## 10. Out of Scope (v1)

SMS ya WhatsApp alerts; user accounts/login (Cognito); farmer-level ya khet-level targeting; scientific dispersion modelling; LLM-generated advisory; mobile app; payments; hardware sensors; ground validation of smoke estimate; configured region ke bahar ke areas.

## 11. Known Limitations (UI me bhi honestly dikhani hain)

- FIRMS **thermal anomalies / active fires** detect karta hai. Har detection crop-residue burning hi ho, ye guaranteed nahi. UI me "possible crop-residue fire" ya "fire detection" likho, "confirmed stubble burning" nahi.
- Satellite pass ke wajah se detection me delay hota hai. "Near real-time" likho, "real-time" nahi.
- Smoke path ek **heuristic estimate** hai (wind direction + speed), dispersion model nahi.
- AQI values modelled hain, ground station readings nahi.
- Thresholds (angle tolerance, attenuation, severity) abhi validated nahi hain, "indicative" label ke saath.

## 12. Assumptions aur Open Questions (owner confirm kare)

| ID | Question / Assumption |
|----|----------------------|
| Q-01 | Product ka naam kya hoga? |
| Q-02 | Operator (individual/company) ka naam, contact email, aur jurisdiction (legal pages ke liye) |
| Q-03 | Target cities ki final list (starter: Delhi, Gurugram, Noida, Ghaziabad, Faridabad, Chandigarh, Ludhiana, Amritsar, Patiala, Jalandhar, Karnal, Panipat, Ambala, Rohtak, Hisar) |
| Q-04 | Source region: kaun se states? (Assumption: Punjab aur Haryana). Neighbouring country ke areas exclude hone chahiye? (Assumption: haan) |
| Q-05 | Officer report public rahegi ya login ke peeche? (Assumption: public, read-only, v1) |
| Q-06 | Open-Meteo free API non-commercial use ke liye hai. Agar product commercial hoga to paid plan chahiye. Product ka nature kya hai? |
| Q-07 | Map tiles ka provider. OpenStreetMap ke standard tile servers heavy production use ke liye nahi hain. Traffic badhne par alternative chahiye |
| Q-08 | Languages: English + Hindi (Assumption). Punjabi chahiye? |
| Q-09 | Analytics chahiye? (Assumption: nahi) |
| Q-10 | Alert cooldown (12h) aur severity thresholds ka final approval (Antigravity propose karega) |
| Q-11 | Advisory content ke sources: kaun si official websites trusted maani jayein |
