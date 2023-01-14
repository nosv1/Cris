use std::collections::HashMap;

use google_sheets4::api::NamedRange;
use serenity::prelude::Context;
use serenity::model::prelude::Message;

use super::super::tepcott;

// pub async fn update_divs(context: &Context, msg: &Message) -> Result<(), Box<dyn std::error::Error>> {
    // println!("{}: {}", msg.timestamp, msg.content);

pub async fn update_divs() -> Result<(), Box<dyn std::error::Error>> {

    let sheets_client = match tepcott::get_sheets_client().await {
        Ok(sheets_client) => sheets_client,
        Err(e) => {
            println!("Error getting sheets client: {:?}", e);
            return Err(e)?;
        }
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
        Err(e) => {
            println!("Error getting spreadsheet: {:?}", e);
            return Err(e)?;
        }
    };
    let spreadsheet_id = match &spreadsheet.spreadsheet_id {
        Some(spreadsheet_id) => spreadsheet_id,
        None => {
            println!("Error: Missing spreadsheet id");
            return Ok(());
        }
    };
    
    let sheets = match tepcott::get_spreadsheet_sheets(spreadsheet.clone()) {
        Ok(sheets) => sheets,
        Err(e) => { 
            println!("Error getting sheets: {:?}", e);
            return Ok(()); 
        }
    };

    let named_ranges = match tepcott::get_spreadsheet_named_ranges(spreadsheet.clone()) {
        Ok(named_ranges) => named_ranges,
        Err(e) => { 
            println!("Error getting named ranges: {:?}", e);
            return Ok(()); 
        }
    };

    let history_drivers_range = named_ranges.get("history_drivers");
    let history_divs_range = named_ranges.get("history_divs");
    let roster_drivers_range = named_ranges.get("roster_drivers");
    let roster_discord_ids_range = named_ranges.get("roster_discord_ids");

    let history_ranges_vec = vec![
        history_drivers_range,
        history_divs_range,
    ];
    let roster_ranges_vec = vec![
        roster_drivers_range,
        roster_discord_ids_range,
    ];

    let mut named_ranges_map: HashMap<String, Vec<Option<&NamedRange>>> = HashMap::new();
    named_ranges_map.insert(
        "history".to_string(), 
        history_ranges_vec.clone()
    );
    named_ranges_map.insert(
        "roster".to_string(), 
        roster_ranges_vec.clone()
    );

    let mut ranges_request = sheets_client
        .spreadsheets()
        .values_batch_get(spreadsheet_id)
        .value_render_option("FORMATTED_VALUE")
        .major_dimension("COLUMNS");

    for sheet_name in named_ranges_map.keys() {
        let ranges_vec = named_ranges_map.get(sheet_name).unwrap();
    
        for range in ranges_vec {
            if range
                .and_then(|range| range.range.as_ref())
                .is_none()
                || range
                    .and_then(|range| range.name.as_ref())
                    .is_none()
            { 
                println!("Missing range or name for sheet: {}, range: {:?}", sheet_name, range);
                return Ok(()); 
            }

            let grid_range = range.as_ref().unwrap().range.as_ref().unwrap();

            let start_row_index = match grid_range.start_row_index {
                Some(start_row_index) => start_row_index,
                None => {
                    println!("Missing start row index for sheet: {}", sheet_name);
                    return Ok(());
                }
            };
            let end_row_index = match grid_range.end_row_index {
                Some(end_row_index) => end_row_index,
                None => {
                    println!("Missing end row index for sheet: {}", sheet_name);
                    return Ok(());
                }
            };
            let start_column_index = match grid_range.start_column_index {
                Some(start_column_index) => start_column_index,
                None => {
                    println!("Missing start column index for sheet: {}", sheet_name);
                    return Ok(());
                }
            };
            let end_column_index = match grid_range.end_column_index {
                Some(end_column_index) => end_column_index,
                None => {
                    println!("Missing end column index for sheet: {}", sheet_name);
                    return Ok(());
                }
            };
            let range_string = format!(
                "'{}'!R{}C{}:R{}C{}",
                sheet_name,
                start_row_index + 1,
                start_column_index + 1,
                end_row_index,
                end_column_index
            );
            ranges_request = ranges_request.add_ranges(&range_string);
        }
    }
    
    let range_values = match ranges_request.doit().await {
        Ok(range_values) => range_values.1,
        Err(e) => {
            println!("Error getting values for sheets: {:?}", e);
            return Ok(());
        }
    };

    if range_values.value_ranges.is_none() { return Ok(()); }

    for values in range_values.value_ranges.unwrap().iter() {
        println!("{:?}", values);
    }

    println!("Divisions updated");

    Ok(())
}