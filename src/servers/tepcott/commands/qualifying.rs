use std::borrow::Cow;
use std::vec;

use serenity::prelude::Context;
use serenity::model::prelude::Message;

extern crate google_sheets4 as sheets4;
use sheets4::api::ValueRange;

use std::collections::HashMap;

use super::super::tepcott;

async fn get_predicted_qualifying_cutoffs() -> Vec<ValueRange> {
    println!("Getting predicted qualifying cutoffs");

    let sheets_client = match tepcott::get_sheets_client().await {
        Ok(sheets_client) => sheets_client,
        Err(_) => return vec![]
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
        Err(_) => return vec![]
    };
    let spreadsheet_id = match spreadsheet.spreadsheet_id.as_ref() {
        Some(spreadsheet_id) => spreadsheet_id,
        None => return vec![],
    };

    let _sheets = match tepcott::get_spreadsheet_sheets(spreadsheet.clone()) {
        Ok(sheets) => sheets,
        Err(_) => { return vec![]; }
    };

    let named_ranges = match tepcott::get_spreadsheet_named_ranges(spreadsheet.clone()) {
        Ok(named_ranges) => named_ranges,
        Err(_) => { return vec![]; }
    };

    let qualifying_average_predicted_cutoffs_range = named_ranges.get("qualifying_average_predicted_cutoffs");
    let qualifying_predicted_number_of_qualifiers_range = named_ranges.get("qualifying_predicted_number_of_qualifiers");

    let qualifying_ranges_vec = vec![
        qualifying_average_predicted_cutoffs_range,
        qualifying_predicted_number_of_qualifiers_range
    ];

    let mut qualifying_ranges_hashmap: HashMap<String, String> = HashMap::new();

    const SHEET_NAME: &str = "qualifying";
    let value_ranges = tepcott::get_range_value_ranges(
        &sheets_client, 
        spreadsheet_id, 
        "ROWS", 
        qualifying_ranges_vec, 
        SHEET_NAME,
        &mut qualifying_ranges_hashmap
    ).await;

    return value_ranges;
}

pub async fn display_cutoffs(ctx: &Context, msg: &Message) {
    let predicted_qualifying_cutoffs = get_predicted_qualifying_cutoffs().await;

    let average_cuttoffs: Vec<Vec<String>> = predicted_qualifying_cutoffs[0].values.clone().unwrap();
    let predicted_number_of_qualifiers: i32 = predicted_qualifying_cutoffs[1].values.clone().unwrap()[0][0].parse().unwrap();
    
    // make an embed
    let mut embed = serenity::builder::CreateEmbed::default();
    embed.color(0x568fd7);
    embed.title("**Predicted Qualifying Cutoffs**");
    
    // load ./season_7_logo.png and set it as the embed thumbnail
    let logo = match std::fs::read(tepcott::SEASON_7_LOGO_PATH) {
        Ok(logo) => logo,
        Err(_) => return
    };
    embed.thumbnail("attachment://season_7_logo.png");
    
    let mut description = String::new();
    // **Predicted qualifiers:** `81`

    // **Division 1:** `1:58.789`
    // **Division 2:** `2:00.139`
    // **Division 3:** `2:00.986`
    // **Division 4:** `2:02.701`

    description.push_str(&format!(
        "**Predicted qualifiers:** `{}`\n\n", 
        predicted_number_of_qualifiers));


    for (_, row) in average_cuttoffs.iter().enumerate() {
        for (j, column) in row.iter().enumerate() {
            description.push_str(&format!(
                "**Division {}:** `{}`\n", 
                j+1, 
                column));
        }
    }

    embed.description(description);

    embed.footer(|f| {
        f.text("Size and number of divisions are undetermined until after qualifying. The predictions above are averages of division sizes 15-18.");
        f
    });
    
    // send the embed
    let _ = msg.channel_id.send_message(&ctx.http, |m| {
        m.embed(|e| {
            e.0 = embed.0;
            e
        });
        m.add_file(serenity::model::channel::AttachmentType::Bytes {
            data: Cow::from(logo),
            filename: "season_7_logo.png".to_string()
        });
        m
    }).await;
}
