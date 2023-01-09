extern crate google_sheets4 as sheets4;
use sheets4::api::{Sheet, NamedRange, BatchUpdateValuesRequest};
use sheets4::hyper::client::HttpConnector;
use sheets4::hyper_rustls::HttpsConnector;
use sheets4::oauth2::{InstalledFlowAuthenticator};
use sheets4::{Result};
use sheets4::{Sheets, oauth2, hyper, hyper_rustls};

use std::collections::HashMap;

// pub const GUILD_ID: &str = "450289520009543690";                 // TEPCOTT
// pub const SUBMISSIONS_CHANNEL_ID: &str = "1058730856073670656";  // #submissions

pub const GUILD_ID: &str = "789181254120505386";                 // Phyner
pub const SUBMISSIONS_CHANNEL_ID: &str = "789182513633427507";   // #private-testing

const CLIENT_SECRET: &str = "src/servers/tepcott/google_api/client_secret.json";  // src/servers/tepcott/tepcott-30c3532764ae.json
const SEASON_7_SPREADSHEET_KEY: &str = "1axNs6RyCy8HE8AEtH5evzBt-cxQyI8YpGutiwY8zfEU";

async fn get_sheets_client() -> Result<Sheets<HttpsConnector<HttpConnector>>>{
    let google_apis_secret_path = std::path::Path::new(CLIENT_SECRET);

    // secret
    let secret: oauth2::ApplicationSecret = oauth2::read_application_secret(google_apis_secret_path)
        .await
        .expect("Error reading client secret file");
        
    // authenticator
    let auth = InstalledFlowAuthenticator::builder(secret, oauth2::InstalledFlowReturnMethod::HTTPRedirect)
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
                    .build()), 
        auth
    );

    Ok(sheets_client)
}


pub async fn submit_quali_time(user_id: &str, lap_time: &str, link: &str) -> Result<bool> {

    println!("Submitting quali time for user {} with lap time {} and link {}", user_id, lap_time, link);

    let sheets_client = match get_sheets_client().await {
        Ok(sheets_client) => sheets_client,
        Err(e) => Err(e)?,
    };

    let spreadsheet = match sheets_client
        .spreadsheets()
        .get(SEASON_7_SPREADSHEET_KEY)
        .include_grid_data(false)
        .doit()
        .await {                                                                // spreadsheet
            Ok(spreadsheet) => spreadsheet.1,
            Err(e) => Err(e)?,
        };
    
        
    // TODO: IDEALLY THE BELOW TWO MATCH STATEMENTS SHOULD BE IN THEIR OWN 'CLASS'
    let mut sheets: HashMap<String, &Sheet> = HashMap::new();
    match &spreadsheet.sheets {                                                 // sheets
        Some(sheets_vec) => {
            for sheet in sheets_vec.iter() {
                match &sheet.properties {
                    Some(properties) => match &properties.title {
                        Some(title) => sheets.insert(title.to_string(), sheet),
                        None => continue,
                    },
                    None => continue,
                };
            }
        }
        None => return Ok(false),
    }
    
    let mut named_ranges: HashMap<String, &NamedRange> = HashMap::new();
    match &spreadsheet.named_ranges {                                           // named ranges
        Some(named_ranges_vec) => {
            for named_range in named_ranges_vec.iter() {
                match &named_range.name {
                    Some(name) => named_ranges.insert(name.to_string(), named_range),
                    None => continue,
                };
            }
        }
        None => return Ok(false),
    }
    // END MATCH STATEMENTS

    let _quali_sheet = sheets.get("qualifying").unwrap();

    let quali_drivers_named_range = named_ranges.get("qualifying_drivers").unwrap();
    let quali_lap_times_named_range = named_ranges.get("qualifying_lap_times").unwrap();

    let quali_drivers_range = quali_drivers_named_range.range.as_ref().unwrap();
    let quali_lap_times_range = quali_lap_times_named_range.range.as_ref().unwrap();

    let mut quali_values = sheets_client.spreadsheets().values_batch_get(
        spreadsheet.spreadsheet_id.as_ref().unwrap()
    )
        .value_render_option("FORMATTED_VALUE")
        .add_ranges(&format!("{}!R{}C{}:R{}C{}", 
            "qualifying", 
            &quali_drivers_range.start_row_index.unwrap() + 1, 
            &quali_drivers_range.start_column_index.unwrap() + 1, 
            &quali_drivers_range.end_row_index.unwrap() + 1, 
            &quali_drivers_range.end_column_index.unwrap() + 1
        ))
        .add_ranges(&format!("{}!R{}C{}:R{}C{}", 
            "qualifying", 
            &quali_lap_times_range.start_row_index.unwrap() + 1,
            &quali_lap_times_range.start_column_index.unwrap() + 1,
            &quali_lap_times_range.end_row_index.unwrap() + 1,
            &quali_lap_times_range.end_column_index.unwrap() + 1
        ))
        .major_dimension("ROWS")
        .doit()
        .await
        .unwrap()
        .1;

    quali_values
        .value_ranges.as_mut().unwrap()[1]
        .values.as_mut().unwrap()[1] = ["1:23.456".to_string()].to_vec();
    
    sheets_client.spreadsheets().values_batch_update(
        BatchUpdateValuesRequest { 
            data: quali_values.value_ranges, 
            include_values_in_response: Some(false), 
            response_date_time_render_option: Some("FORMATTED_STRING".to_string()),
            response_value_render_option: Some("FORMATTED_VALUE".to_string()),
            value_input_option: Some("USER_ENTERED".to_string()),
        }, 
        spreadsheet.spreadsheet_id.as_ref().unwrap()
    )
        .doit()
        .await
        .unwrap();

    println!("Submitted quali time for user {} with lap time {} and link {}", user_id, lap_time, link);

    Ok(true)


}