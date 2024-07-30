# kashBets Account Creation

This script automates the process of creating accounts on the `kashbets.io` platform, including generating temporary emails, verifying them, and spinning invite bonuses.

## Features

- **Proxy Support:** The script uses proxies for making requests to avoid IP blocking.
- **Multi-threading:** You can run multiple threads to create multiple accounts simultaneously.
- **Email Verification:** The script fetches the verification link from the temporary email and verifies the account.
- **Invite Bonus:** After account creation, the script spins the invite bonus.

## Prerequisites

- Python 3.7 or higher
- `requests` library
- A list of proxies in the `proxies.txt` file

