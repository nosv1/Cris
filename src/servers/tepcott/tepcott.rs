extern crate google_sheets4 as sheets4;
use std::collections::HashMap;

use sheets4::api::{Spreadsheet, Sheet, NamedRange};
use sheets4::hyper::client::HttpConnector;
use sheets4::hyper_rustls::HttpsConnector;
use sheets4::oauth2::InstalledFlowAuthenticator;
use sheets4::Result as SheetsResult;
use sheets4::{hyper, hyper_rustls, oauth2, Sheets};

pub const GUILD_ID: &str = "450289520009543690";                 // TEPCOTT
pub const SUBMISSIONS_CHANNEL_ID: &str = "1058730856073670656";  // #submissions

// pub const GUILD_ID: &str = "789181254120505386"; // Phyner
// pub const SUBMISSIONS_CHANNEL_ID: &str = "789182513633427507"; // #private-testing

const CLIENT_SECRET: &str = "src/servers/tepcott/google_api/client_secret.json"; // src/servers/tepcott/tepcott-30c3532764ae.json
pub const SEASON_7_SPREADSHEET_KEY: &str = "1axNs6RyCy8HE8AEtH5evzBt-cxQyI8YpGutiwY8zfEU";

pub fn a1_to_r1c1(a1_range: String) -> String {
    let parts = a1_range.split("!").collect::<Vec<&str>>();
    let sheet_name = parts[0];
    let a1_range = parts[1];
    
    let cell_parts = a1_range.split(":").collect::<Vec<&str>>();
    let start_cell = cell_parts[0];
    let end_cell = cell_parts[1];

    let start_col = start_cell.chars()
        .take_while(|c| c.is_alphabetic())
        .map(|c| (c as u8 - 64) as i32)
        .fold(0, |x, y| x * 26 + y);
    let start_row: i32 = start_cell.chars()
        .skip_while(|ch| !ch.is_numeric())
        .collect::<String>().parse().unwrap();
    let end_col = end_cell.chars()
        .take_while(|c| c.is_alphabetic())
        .map(|c| (c as u8 - 64) as i32)
        .fold(0, |x, y| x * 26 + y);
    let end_row: i32 = end_cell.chars()
        .skip_while(|ch| !ch.is_numeric())
        .collect::<String>().parse().unwrap();

    let r1c1_range = format!("{}!R{}C{}:R{}C{}", sheet_name, start_row, start_col, end_row, end_col);
    return r1c1_range;
}

// return hashmap or error
pub fn get_spreadsheet_sheets(spreadsheet: Spreadsheet) -> Result<HashMap<String, Sheet>, String> {
    let mut sheets: HashMap<String, Sheet> = HashMap::new(); // sheets
    for sheet in spreadsheet.sheets.unwrap().iter() {
        let properties = sheet.properties.as_ref();
        let title = sheet.properties.as_ref()
            .and_then(|p| p.title.as_ref());
        if properties.is_none() || title.is_none() {
            return Err("Missing properties or title".to_string());
        } else {
            let sheet = sheet.clone();
            sheets.insert(title.unwrap().to_string(), sheet);
        }
    }
    Ok(sheets)
}


pub fn get_spreadsheet_named_ranges(spreadsheet: Spreadsheet) -> Result<HashMap<String, NamedRange>, String> {
    let mut named_ranges: HashMap<String, NamedRange> = HashMap::new();
    for named_range in spreadsheet.named_ranges.unwrap().iter() {
        let name = named_range.name.as_ref();
        let range = named_range.range.as_ref();
        if name.is_none() || range.is_none() {
            return Err("Missing name or range".to_string());
        } else {
            named_ranges.insert(name.unwrap().to_string(), named_range.clone());
        }
    }
    Ok(named_ranges)
}


pub async fn get_sheets_client() -> SheetsResult<Sheets<HttpsConnector<HttpConnector>>> {
    let google_apis_secret_path = std::path::Path::new(CLIENT_SECRET);

    // secret
    let secret: oauth2::ApplicationSecret =
        oauth2::read_application_secret(google_apis_secret_path)
            .await
            .expect("Error reading client secret file");

    // authenticator
    let auth = InstalledFlowAuthenticator::builder(
        secret,
        oauth2::InstalledFlowReturnMethod::HTTPRedirect,
    )
    .persist_tokens_to_disk("src/servers/tepcott/google_api/token.json")
    .build()
    .await
    .expect("Error building authenticator");

    // sheets client
    let sheets_client = Sheets::new(
        hyper::Client::builder().build(
            hyper_rustls::HttpsConnectorBuilder::new()
                .with_native_roots()
                .https_or_http()
                .enable_http1()
                .enable_http2()
                .build(),
        ),
        auth,
    );

    Ok(sheets_client)
}