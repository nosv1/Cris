use std::collections::HashMap;

use serenity::prelude::{Context, Mentionable};
use serenity::model::prelude::{Message, Guild, Member, RoleId, ChannelId};

use super::super::tepcott;

const DIV_ROLES_IDS: [&str; 7] = [
    "",
    "702192471316103235", 
    "702192533765357670", 
    "702192563582402650", 
    "702192590560428173", 
    "702192621891747981",
    "702192638341939240"
];

const DIV_CHANNEL_IDS: [&str; 7] = [
    "",
    "702242781946576936", 
    "702244420153638983", 
    "702244753038770207", 
    "702245227888640091", 
    "796751429636980746",
    "796751528861237258"
];

pub async fn update_division_roles(context: &Context, message: &Message, guild: &Guild) -> Result<(), Box<dyn std::error::Error>> {
    let msg = message.channel_id.say(&context.http, "Updating divisions...").await?;

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
    
    let _sheets = match tepcott::get_spreadsheet_sheets(spreadsheet.clone()) {
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

    let roster_divs_range = named_ranges.get("roster_divs");
    let roster_discord_ids_range = named_ranges.get("roster_discord_ids");

    let roster_ranges_vec = vec![
        roster_divs_range,
        roster_discord_ids_range,
    ];

    let mut ranges_hashmap: HashMap<String, String> = HashMap::new();

    let mut ranges_request = sheets_client
        .spreadsheets()
        .values_batch_get(spreadsheet_id)
        .value_render_option("FORMATTED_VALUE")
        .major_dimension("COLUMNS");
    
    for range in roster_ranges_vec {
        if range
            .and_then(|range| range.range.as_ref())
            .is_none()
            || range
                .and_then(|range| range.name.as_ref())
                .is_none()
        { 
            println!("Error: Missing range or name for named range: {:?}", range);
            return Ok(()); 
        }

        let grid_range = range.as_ref().unwrap().range.as_ref().unwrap();
        let name = range.as_ref().unwrap().name.as_ref().unwrap();

        let start_row_index = match grid_range.start_row_index {
            Some(start_row_index) => start_row_index,
            None => {
                println!("Missing start row index for range: {:?}", range);
                return Ok(());
            }
        };
        let end_row_index = match grid_range.end_row_index {
            Some(end_row_index) => end_row_index,
            None => {
                println!("Missing end row index for range: {:?}", range);
                return Ok(());
            }
        };
        let start_column_index = match grid_range.start_column_index {
            Some(start_column_index) => start_column_index,
            None => {
                println!("Missing start column index for range: {:?}", range);
                return Ok(());
            }
        };
        let end_column_index = match grid_range.end_column_index {
            Some(end_column_index) => end_column_index,
            None => {
                println!("Missing end column index for range: {:?}", range);
                return Ok(());
            }
        };
        let range_string = format!(
            "{}!R{}C{}:R{}C{}",
            "roster",
            start_row_index + 1,
            start_column_index + 1,
            end_row_index,
            end_column_index
        );
        ranges_request = ranges_request.add_ranges(&range_string);
        ranges_hashmap.insert(range_string, name.clone());
    }
    
    let range_values = match ranges_request.doit().await {
        Ok(range_values) => range_values.1,
        Err(e) => {
            println!("Error getting values for sheets: {:?}", e);
            return Ok(());
        }
    };

    if range_values.value_ranges.is_none() { 
        println!("Missing value ranges");
        return Ok(()); 
    }

    let mut roster_divs_values: Vec<String> = vec![];
    let mut roster_discord_ids_values: Vec<String> = vec![];

    for value_range in range_values.value_ranges.unwrap().iter() {
        if value_range.range.is_none() || value_range.values.is_none() {
            println!("Missing range or values for value range: {:?}", value_range.range);
            return Ok(());
        }
        let range = tepcott::a1_to_r1c1(value_range.range.as_ref().unwrap().to_string());
        let name = ranges_hashmap.get(&range).unwrap();
        let values = value_range.values.as_ref().unwrap();
        match name.as_str() {
            "roster_divs" => {
                roster_divs_values = values[0].clone();
            },
            "roster_discord_ids" => {
                roster_discord_ids_values = values[0].clone();
            },
            _ => {
                println!("Unknown range name: {}", name);
                return Ok(());
            }
        }
    }
    

    let mut drivers: HashMap<String, usize> = HashMap::new();  // discord_id, division

    for (i, discord_id) in roster_discord_ids_values.iter().enumerate() {
        let division: usize;
        if i < roster_divs_values.len() && roster_divs_values[i] != "" {
            division = roster_divs_values[i].parse().unwrap();
        } else {
            division = 0;
        }
        drivers.insert(discord_id.to_string(), division);
    }

    let mut guild_roles: HashMap<RoleId, Vec<Member>> = HashMap::new();  // role_id, members
    for member in guild.members.values() {
        for role_id in member.roles.iter() {
            guild_roles
                .entry(*role_id)
                .or_insert(vec![])
                .push(member.clone());
        }
    }
    
    for (role_id, members) in guild_roles.iter_mut() {
        let role = guild.roles.get(role_id).unwrap();
        if !role.name.to_lowercase().starts_with("div") { continue; }
        let role_division: usize = role.name
            .to_lowercase()
            .replace("div", "")
            .parse().unwrap();

        for member in members {
            let member_id = member.user.id.to_string();

            if !drivers.contains_key(&member_id) { continue; }
            let _ = message.channel_id.say(
                &context.http, 
                format!("{} is not on the roster...", member.mention())
            ).await;

            let driver_division = drivers.get(&member_id).unwrap().clone();
            drivers.remove(&member_id);
            
            if driver_division == role_division { continue; }            // driver is in correct division

            let previous_channel_id: ChannelId = ChannelId(DIV_CHANNEL_IDS[role_division].parse().unwrap());
            member.remove_role(context.http.clone(), role_id).await?;
            previous_channel_id.say(
                &context.http, 
                format!("{} was removed from Division {}.", member.mention(), role_division)
            ).await?;
            println!("Removed {} from {}", member.display_name(), role.name);
            
            if driver_division == 0 { continue; }                       // driver is not in a division
            let driver_division_role_id = DIV_ROLES_IDS[driver_division].parse().unwrap();
            let driver_division_role = guild.roles.get(&RoleId(driver_division_role_id)).unwrap();

            let new_channel_id: ChannelId = ChannelId(DIV_CHANNEL_IDS[driver_division].parse().unwrap());
            member.add_role(context.http.clone(), driver_division_role_id).await?;
            new_channel_id.say(
                &context.http, 
                format!("Welcome to Division {}, {}!", driver_division, member.mention())
            ).await?;
            println!("Added {} to {}", member.display_name(), driver_division_role.name);
        }
    }

    for (discord_id, division) in drivers {
        if division == 0 { continue; }  // driver is not in any division, they were already removed, if they were, in the loop above

        let driver_division_role_id = DIV_ROLES_IDS[division].parse().unwrap();
        let driver_division_role = guild.roles.get(&RoleId(driver_division_role_id)).unwrap();

        let member_id = discord_id.parse().unwrap();
        let member = guild.members.get(&member_id).unwrap();

        let new_channel_id: ChannelId = ChannelId(DIV_CHANNEL_IDS[division].parse().unwrap());

        member.clone().add_role(context.http.clone(), driver_division_role_id).await?;
        new_channel_id.say(
            &context.http, 
            format!("Welcome to Division {}, {}!", division, member.mention())
        ).await?;
        println!("Added {} to {}", member.display_name(), driver_division_role.name);
    }
    
    msg.channel_id.edit_message(
        &context.http, 
        msg.id,
        |m| {
        m.content("Division roles updated.")
    }).await?;
    Ok(())
}