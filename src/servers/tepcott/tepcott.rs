extern crate google_sheets4 as sheets4;
use sheets4::{Result};
use sheets4::{Sheets, oauth2, hyper, hyper_rustls};

// pub const GUILD_ID: &str = "450289520009543690";                 // TEPCOTT
// pub const SUBMISSIONS_CHANNEL_ID: &str = "1058730856073670656";  // #submissions

pub const GUILD_ID: &str = "789181254120505386";                 // Phyner
pub const SUBMISSIONS_CHANNEL_ID: &str = "789182513633427507";   // #private-testing

const GOOGLE_APIS_SECRET: &str = "tepcott-30c3532764ae.json";  // src/servers/tepcott/tepcott-30c3532764ae.json
const SEASON_7_SPREADSHEET_KEY: &str = "1axNs6RyCy8HE8AEtH5evzBt-cxQyI8YpGutiwY8zfEU";

async fn open_workbook() -> Result<sheets4::api::Spreadsheet> {

    // secret file
    let secret = oauth2::
        read_application_secret(GOOGLE_APIS_SECRET)
            .await
            .expect("Failed to read secret file");
        
        let auth = oauth2::InstalledFlowAuthenticator::builder(
            secret,
            oauth2::InstalledFlowReturnMethod::HTTPRedirect,
        )
            .build()
            .await
            .unwrap();

    // sheets client
    let hub = Sheets::new(
        hyper::Client::builder().build(
                hyper_rustls::HttpsConnectorBuilder::new()
                    .with_native_roots()
                    .https_or_http()
                    .enable_http1()
                    .enable_http2()
                    .build()), 
        auth
    );

    // open spreadsheet
    let spreadsheet = hub
        .spreadsheets()
        .get(SEASON_7_SPREADSHEET_KEY)
        .doit()
        .await
        .expect("Failed to open spreadsheet");
        
    Ok(spreadsheet.1)

}


pub async fn submit_quali_time(user_id: &str, lap_time: &str, link: &str) {

    let spreadsheet = open_workbook().await;
    println!("{:?}", spreadsheet);
}