## Current Functionality
- [x] Read #submissions for qualifying submissions and post them to the spreadsheet.
- [x] Automatically update division roles upon command. `!updatedivs`
    - [x] Also updates discord names to be `social_club (discord)`
- [x] Display the predicted qualifying cutoffs for each division. `!cutoffs`
- [ ] Convert everything to python for the sake of slash commands
- [ ] Add slash command for reserves. `/reserves`
- [x] Add slash command for starting orders. `/starting order`

## Libraries and Tools Used
- [ChatGPT](https://openai.com/blog/chatgpt/): An AI model for natural language processing and text generation.
- [GitHub Copilot](https://github.com/features/copilot): A tool for helping developers work more efficiently with GitHub.
- [Serenity](https://docs.rs/serenity/latest/serenity/): A Rust library for building fast and efficient Discord bots.
- [google_sheets4](https://docs.rs/google-sheets4/latest/google_sheets4/): An API that allows communication and data manipulation with Google Sheets.

## Notes for Use
- The project requires a missing `.env` file, which should contain the variable `DISCORD_BOT_TOKEN`.
- The project also requires a `client_secret.json` file which is missing in the `servers/tepcott/google_api` folder. This file can be obtained from Google's OAuth credentials.

## License
This project is licensed under the MIT License.

Copyright (c) [year] [copyright holders]

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

- The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
- The software is provided "AS IS", without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose and non-infringement.
- In no event shall the authors or copyright holders be liable for any claim, damages or other liability, whether in an action of contract, tort or otherwise, arising from, out of or in connection with the software or the use or other dealings in the software.
