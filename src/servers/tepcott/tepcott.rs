extern crate google_sheets4 as sheets4;
use sheets4::api::{BatchUpdateValuesRequest, NamedRange, Sheet};
use sheets4::hyper::client::HttpConnector;
use sheets4::hyper_rustls::HttpsConnector;
use sheets4::oauth2::InstalledFlowAuthenticator;
use sheets4::Result;
use sheets4::{hyper, hyper_rustls, oauth2, Sheets};

use std::collections::HashMap;

pub const GUILD_ID: &str = "450289520009543690";                 // TEPCOTT
pub const SUBMISSIONS_CHANNEL_ID: &str = "1058730856073670656";  // #submissions

// pub const GUILD_ID: &str = "789181254120505386"; // Phyner
// pub const SUBMISSIONS_CHANNEL_ID: &str = "789182513633427507"; // #private-testing

const CLIENT_SECRET: &str = "src/servers/tepcott/google_api/client_secret.json"; // src/servers/tepcott/tepcott-30c3532764ae.json
const SEASON_7_SPREADSHEET_KEY: &str = "1axNs6RyCy8HE8AEtH5evzBt-cxQyI8YpGutiwY8zfEU";

fn a1_to_r1c1(a1_range: String) -> String {
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

async fn get_sheets_client() -> Result<Sheets<HttpsConnector<HttpConnector>>> {
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

pub async fn submit_quali_time(
    driver: &str,
    user_id: &str,
    timestamp: &str,
    lap_time: &str,
    link: &str,
) -> Result<bool> {
    println!(
        "Submitting quali time for {} with lap time {} and link {}",
        driver, lap_time, link
    );

    let sheets_client = match get_sheets_client().await {
        Ok(sheets_client) => sheets_client,
        Err(e) => Err(e)?,
    };

    let spreadsheet = match sheets_client
        .spreadsheets()
        .get(SEASON_7_SPREADSHEET_KEY)
        .include_grid_data(false)
        .doit()
        .await
    {
        // spreadsheet
        Ok(spreadsheet) => spreadsheet.1,
        Err(e) => Err(e)?,
    };
    let spreadsheet_id = match &spreadsheet.spreadsheet_id {
        Some(spreadsheet_id) => spreadsheet_id,
        None => return Ok(false),
    };

    // TODO: IDEALLY THE BELOW TWO LOOPS SHOULD BE IN THEIR OWN 'CLASS'
    let mut sheets: HashMap<String, &Sheet> = HashMap::new(); // sheets
    for sheet in spreadsheet.sheets.unwrap().iter() {
        let properties = sheet.properties.as_ref();
        let title = sheet.properties.as_ref()
            .and_then(|p| p.title.as_ref());
        if properties.is_none() || title.is_none() {
            return Ok(false);
        } else {
            sheets.insert(title.unwrap().to_string(), sheet);
        }
    }

    let mut named_ranges: HashMap<String, &NamedRange> = HashMap::new();
    for named_range in spreadsheet.named_ranges.as_ref().unwrap().iter() {
        let name = named_range.name.as_ref();
        if name.is_none() {
            return Ok(false);
        } else {
            named_ranges.insert(name.unwrap().to_string(), named_range);
        }
    }
    // END TODO

    let quali_submissions_drivers_range = named_ranges.get("quali_submissions_drivers");
    let quali_submissions_discord_ids_range = named_ranges.get("quali_submissions_discord_ids");
    let quali_submissions_timestamps_range = named_ranges.get("quali_submissions_timestamps");
    let quali_submissions_lap_times_range = named_ranges.get("quali_submissions_lap_times");
    let quali_submissions_proofs_range = named_ranges.get("quali_submissions_proofs");

    let quali_submission_ranges_vec = vec![
        quali_submissions_drivers_range,
        quali_submissions_discord_ids_range,
        quali_submissions_timestamps_range,
        quali_submissions_lap_times_range,
        quali_submissions_proofs_range,
    ];

    let mut quali_submission_ranges_hashmap: HashMap<String, String> = HashMap::new();

    let mut quali_submissions_request = sheets_client
        .spreadsheets()
        .values_batch_get(spreadsheet_id)
        .value_render_option("FORMATTED_VALUE")
        .major_dimension("COLUMNS");

    for quali_submission_range in quali_submission_ranges_vec.iter() {
        if quali_submission_range
            .and_then(|range| range.range.as_ref())
            .is_none()
            || quali_submission_range
                .and_then(|range| range.name.as_ref())
                .is_none()
        {
            return Ok(false);
        }
        let range = quali_submission_range.as_ref().unwrap()
            .range.as_ref().unwrap();
        let name = quali_submission_range.as_ref().unwrap()
            .name.as_ref().unwrap();

        let start_row_index = match &range.start_row_index {
            Some(start_row_index) => start_row_index,
            None => return Ok(false),
        };
        let start_column_index = match &range.start_column_index {
            Some(start_column_index) => start_column_index,
            None => return Ok(false),
        };
        let end_row_index = match &range.end_row_index {
            Some(end_row_index) => end_row_index,
            None => return Ok(false),
        };
        let end_column_index = match &range.end_column_index {
            Some(end_column_index) => end_column_index,
            None => return Ok(false),
        };
        let range_string = format!(
            "{}!R{}C{}:R{}C{}",
            "'quali submissions'",
            start_row_index + 1,
            start_column_index + 1,
            end_row_index,
            end_column_index
        );
        quali_submissions_request = quali_submissions_request.add_ranges(&range_string);
        quali_submission_ranges_hashmap.insert(range_string, name.clone());
    }

    let mut quali_submissions_values = match quali_submissions_request.doit().await {
        Ok(quali_submissions_request) => quali_submissions_request.1,
        Err(e) => Err(e)?,
    };

    if quali_submissions_values.value_ranges.is_none() { return Ok(false); }

    for value_range in quali_submissions_values.value_ranges.as_mut().unwrap().iter_mut() {
        if value_range.range.is_none() || value_range.values.is_none() {
            return Ok(false);
        }
        let range = a1_to_r1c1(value_range.range.clone().unwrap());
        let name = quali_submission_ranges_hashmap.get(&range).unwrap();
        let values = value_range.values.as_mut().unwrap();
        match name.as_str() {
            "quali_submissions_drivers" => {
                values[0].push(driver.to_string());
            },
            "quali_submissions_discord_ids" => {
                values[0].push(user_id.to_string());
            },
            "quali_submissions_timestamps" => {
                values[0].push(timestamp.to_string());
            },
            "quali_submissions_lap_times" => {
                values[0].push(lap_time.to_string());
            },
            "quali_submissions_proofs" => {
                values[0].push(link.to_string());
            },
            _ => return Ok(false),
        }
    }

    sheets_client.spreadsheets().values_batch_update(
        BatchUpdateValuesRequest {
            data: quali_submissions_values.value_ranges,
            include_values_in_response: Some(false),
            response_date_time_render_option: Some("FORMATTED_STRING".to_string()),
            response_value_render_option: Some("FORMATTED_VALUE".to_string()),
            value_input_option: Some("USER_ENTERED".to_string()),
        },
        &spreadsheet_id
    )
        .doit()
        .await?;
        
    println!(
        "{}: {} submitted a lap time of {}s with proof {} to the spreadsheet", 
        timestamp, driver, lap_time, link
    );

    Ok(true)
}