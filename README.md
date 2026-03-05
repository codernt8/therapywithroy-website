# Therapy with Roy — Website

Website for [therapywithroy.co.uk](https://therapywithroy.co.uk) — Roy Lam, MBACP Registered Counsellor.

## Hosting

- **Host:** Netlify (free tier)
- **Deployment:** Automatic — every push to `main` triggers a live deploy (~30 seconds)
- **Domain:** therapywithroy.co.uk (managed via Netlify DNS)

## File Reference

| File | Purpose |
|---|---|
| `index.html` | Main single-page website — all sections (hero, about, services, FAQ, booking) |
| `privacy-policy.html` | GDPR-compliant privacy policy |
| `thank-you.html` | Post-booking confirmation page — fires GA4 `booking_complete` conversion event |
| `client-agreement.html` | Client agreement / terms of service |
| `roy pic.jpg` | Roy's profile photo (used in About section) |
| `micke-lindstrom-I3GuNBeDerI-unsplash.jpg` | Background landscape image (Who I Help section) |
| `BACP Logo - 397064.png` | BACP membership logo (footer) |

## Key Integrations

| Tool | Purpose | Notes |
|---|---|---|
| Acuity Scheduling | Bookings & payments | Owner ID: 38582431. Modal popup on site. Redirect to `/thank-you.html` after booking for GA4 tracking. |
| Google Analytics 4 | Analytics | ID: G-EZDPQG16PQ. Loads only after cookie consent. |
| Stripe | Payments | Via Acuity (live mode) |
| Google Meet | Sessions | Link sent automatically by Acuity |
| DocuSeal | Client agreement e-signatures | Free tier |

## Services & Pricing

| Service | Duration | Fee |
|---|---|---|
| Free Initial Consultation | 30 mins | Free |
| Individual Therapy | 50 mins | £80 |
| Couples Therapy | 50 mins | £120 |

## Therapist Details

- **Name:** Roy Lam (Ka Yiu Lam)
- **BACP:** Registered Member No. 397064
- **Qualifications:** MSocSc Counselling, University of Hong Kong (2017)
- **Languages:** English & Cantonese
- **Availability:** Monday–Friday, 9am–7pm UK time
- **Email:** roy@therapywithroy.co.uk
- **Phone:** 07824 426000

## Making Changes

1. Edit the relevant file locally
2. Commit and push to `main`
3. Netlify deploys automatically — live within ~30 seconds

Alternatively, files can be edited directly via the GitHub web interface.

## Outstanding Actions

- [ ] Configure Acuity post-booking redirect to `https://therapywithroy.co.uk/thank-you.html`
- [ ] Complete ICO registration and update registration number in `index.html` footer and `privacy-policy.html`
- [ ] Confirm supervision arrangements
