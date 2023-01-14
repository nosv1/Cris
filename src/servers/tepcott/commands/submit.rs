use std::str::Split;

use regex::Regex;

use serenity::prelude::Context;
use serenity::model::prelude::Message;

extern crate google_sheets4 as sheets4;
use sheets4::api::{BatchUpdateValuesRequest};
use sheets4::Result as SheetsResult;

use std::collections::HashMap;

use super::super::tepcott;

async fn submit_quali_time(
    driver: &str,
    user_id: &str,
    timestamp: &str,
    lap_time: &str,
    link: &str,
) -> SheetsResult<bool> {
    println!(
        "Submitting quali time for user {} with lap time {} and link {}",
        user_id, lap_time, link
    );

    let sheets_client = match tepcott::get_sheets_client().await {
        Ok(sheets_client) => sheets_client,
        Err(e) => Err(e)?,
    };

    let spreadsheet = match sheets_client
        .spreadsheets()
        .get(tepcott::SEASON_7_SPREADSHEET_KEY)
        .include_grid_data(false)
        .doit()
        .await
    {
        // spreadsheet
        Ok(spreadsheet) => spreadsheet.1,
        Err(e) => Err(e)?,
    };
    let spreadsheet_id = match spreadsheet.spreadsheet_id.as_ref() {
        Some(spreadsheet_id) => spreadsheet_id,
        None => return Ok(false),
    };

    let _sheets = match tepcott::get_spreadsheet_sheets(spreadsheet.clone()) {
        Ok(sheets) => sheets,
        Err(_) => { return Ok(false); }
    };

    let named_ranges = match tepcott::get_spreadsheet_named_ranges(spreadsheet.clone()) {
        Ok(named_ranges) => named_ranges,
        Err(_) => { return Ok(false); }
    };
    
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
        let range = tepcott::a1_to_r1c1(value_range.range.clone().unwrap());
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

    println!("Submitted quali time for user {} with lap time {} and link {}", user_id, lap_time, link);

    Ok(true)
}

pub async fn submit(context: &Context, msg: &Message, mut split_message: Split<'_, &str>) -> Result<(), Box<dyn std::error::Error>> {
    // println with timestamp
    println!("{}: {}", msg.timestamp, msg.content);

    let guild_id = match msg.guild_id {
        Some(guild_id) => guild_id,
        None => return Ok(()),
    };

    let time = split_message.next();
    let link = split_message.next();
    println!("time: {:?}, link: {:?}", time, link);

    if time.is_none() || link.is_none() {                                       // check valid number of arguments
        // let _ = msg.channel_id.say(
        //     &context.http, 
        //     "Invalid number of arguments. Please use the following format: !submit <MM:SS.mmm> <weblink to your video/screenshot>"
        // )
        //     .await;
        return Ok(());
    }

    
    let time_format = Regex::new(r"^\d{1,2}:\d{2}\.\d{3}$").unwrap();
    if !time_format.is_match(time.unwrap()) {                              // check valid time format
        println!("Invalid time format");
        // let _ = msg.channel_id.say(
        //     &context.http, 
        //     "Invalid time format. Please use the following format: MM:SS.mmm"
        // )
        //     .await;
        return Ok(());
    }

    let link_format = Regex::new(r"^(https?://)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$").unwrap();
    if !link_format.is_match(link.unwrap()) {                              // check valid link format
        println!("Invalid link format");
        // return error message if invalid link format
        // let _ = msg.channel_id.say(
        //     &context.http,
        //     "Invalid link format. Please provide a valid weblink.")
        //     .await;
        return Ok(());
    }

    // if valid time and link,
    let _ = submit_quali_time(
        &msg.author
            .nick_in(&context.http, guild_id)
            .await
            .unwrap_or_else(|| msg.author.name.clone()),
        &msg.author.id.0.to_string().as_str(),
        &msg.timestamp.to_string(),
        time.unwrap(), 
        link.unwrap()
    ).await;

    Ok(())
    

}