def create_excel_report_for_building(building: str, date_from: str, date_to: str, period_type: str) -> str:
    df = get_report_by_building_and_date_range(building, date_from, date_to)
    
    building_folder = os.path.join(REPORTS_DIR, building)
    os.makedirs(building_folder, exist_ok=True)
    
    now = datetime.now()
    date_from_display = datetime.strptime(date_from, "%Y-%m-%d").strftime("%d.%m.%Y")
    date_to_display = datetime.strptime(date_to, "%Y-%m-%d").strftime("%d.%m.%Y")
    
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    
    if period_type == "daily":
        filename = os.path.join(building_folder, f"report_{building}_daily_{date_from}_{timestamp}.xlsx")
        sheet_title = f"отчёт за {date_from_display}"
    elif period_type == "weekly":
        filename = os.path.join(building_folder, f"report_{building}_weekly_{date_from}_to_{date_to}_{timestamp}.xlsx")
        sheet_title = f"отчёт за период {date_from_display} - {date_to_display}"
    else:
        month_name = now.strftime("%B %Y")
        filename = os.path.join(building_folder, f"report_{building}_monthly_{now.strftime('%Y_%m')}_{timestamp}.xlsx")
        sheet_title = f"отчёт за {month_name}"
    
    categories_1_4 = ["1-4 класс", "ОВЗ и инвалиды 1-4 класс"]
    categories_5_11 = [
        "Без субсидии", "Малообеспеченные", "Многодетные",
        "Участники боевых действий", "Семьи в ТЖС", "С нарушениями здоровья",
        "Семьи военнослужащих", "ОВЗ и инвалиды 5-11", "Кадетские классы"
    ]
    
    classes_by_stage = {
        "1": [f"{g}.{l}" for g in ["1", "2", "3", "4"] for l in range(1, 10)],
        "2": [f"{g}.{l}" for g in ["5", "6", "7", "8", "9"] for l in range(1, 10)],
        "3": ["10.1", "10.2", "11.1", "11.2"]
    }
    
    stage_info = {
        "1": {"sheet_name": "1-4 классы", "categories": categories_1_4, "all_classes": classes_by_stage["1"]},
        "2": {"sheet_name": "5-9 классы", "categories": categories_5_11, "all_classes": classes_by_stage["2"]},
        "3": {"sheet_name": "10-11 классы", "categories": categories_5_11, "all_classes": classes_by_stage["3"]}
    }
    
    if building == "Танкистов":
        del stage_info["3"]
    
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        # Основные листы по ступеням
        for stage_code, info in stage_info.items():
            sheet_name = info["sheet_name"]
            all_categories = info["categories"]
            all_classes = info["all_classes"]
            
            stage_df = df[df['stage'] == stage_code] if not df.empty else pd.DataFrame()
            
            data_dict = {}
            if not stage_df.empty:
                for _, row in stage_df.iterrows():
                    class_name = row['class_name']
                    category = row['category']
                    quantity = row['quantity']
                    if class_name not in data_dict:
                        data_dict[class_name] = {}
                    data_dict[class_name][category] = quantity
            
            data = []
            for category in all_categories:
                row = {"Категория": category}
                for class_name in all_classes:
                    if class_name in data_dict and category in data_dict[class_name]:
                        row[class_name] = data_dict[class_name][category]
                    else:
                        row[class_name] = 0
                data.append(row)
            
            existing_classes = [c for c in all_classes if any(row[c] > 0 for row in data)]
            if not existing_classes and not stage_df.empty:
                existing_classes = all_classes[:5]
            if not existing_classes:
                existing_classes = all_classes[:5]
            
            filtered_data = []
            for row in data:
                filtered_row = {"Категория": row["Категория"]}
                for class_name in existing_classes:
                    filtered_row[class_name] = row[class_name]
                filtered_row["ИТОГО по категории"] = sum(row[class_name] for class_name in existing_classes)
                filtered_data.append(filtered_row)
            
            result_df = pd.DataFrame(filtered_data)
            
            totals_by_class = {"Категория": "ВСЕГО по классу"}
            grand_total = 0
            for class_name in existing_classes:
                class_total = result_df[class_name].sum()
                totals_by_class[class_name] = class_total
                grand_total += class_total
            totals_by_class["ИТОГО по категории"] = grand_total
            result_df = pd.concat([result_df, pd.DataFrame([totals_by_class])], ignore_index=True)
            
            result_df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=3)
            
            worksheet = writer.sheets[sheet_name]
            
            worksheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(existing_classes)+2)
            worksheet.cell(row=1, column=1, value=sheet_title)
            worksheet.cell(row=1, column=1).font = Font(size=14, bold=True)
            worksheet.cell(row=1, column=1).alignment = Alignment(horizontal='center')
            
            for col, class_name in enumerate(existing_classes, 2):
                cell = worksheet.cell(row=3, column=col, value=class_name)
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal='center')
            
            cell = worksheet.cell(row=3, column=len(existing_classes)+2, value="ИТОГО по категории")
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
            worksheet.cell(row=3, column=1, value="Категория")
            worksheet.cell(row=3, column=1).font = Font(bold=True)
            worksheet.cell(row=3, column=1).alignment = Alignment(horizontal='center')
            
            thin_border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
            max_row = worksheet.max_row
            max_col = len(existing_classes) + 2
            
            for row in range(1, max_row + 1):
                for col in range(1, max_col + 1):
                    cell = worksheet.cell(row=row, column=col)
                    cell.border = thin_border
                    if row >= 3:
                        cell.alignment = Alignment(horizontal='center', vertical='center')
                if row >= 4:
                    worksheet.cell(row=row, column=1).alignment = Alignment(horizontal='left', vertical='center')
            
            for col in range(1, max_col + 1):
                max_length = 0
                for row in range(1, max_row + 1):
                    cell_value = worksheet.cell(row=row, column=col).value
                    if cell_value:
                        max_length = max(max_length, len(str(cell_value)))
                adjusted_width = min(max_length + 2, 35)
                worksheet.column_dimensions[get_column_letter(col)].width = adjusted_width
            
            worksheet.column_dimensions['A'].width = 30
        
        # ========== ЛИСТ ДЛЯ НАДОМНОГО ОТДЕЛЕНИЯ (только для Марченко) ==========
        if building == "Марченко":
            home_df = get_home_requests("Надомное", date_from, date_to)
            
            if not home_df.empty:
                classes = sorted(home_df["class_name"].unique())
                categories = categories_5_11
                
                data = []
                for category in categories:
                    row = {"Категория": category}
                    for class_name in classes:
                        subset = home_df[(home_df["category"] == category) & (home_df["class_name"] == class_name)]
                        row[class_name] = subset["quantity"].sum() if not subset.empty else 0
                    data.append(row)
                
                result_df = pd.DataFrame(data)
                
                totals_by_class = {"Категория": "ВСЕГО по классу"}
                grand_total = 0
                for class_name in classes:
                    class_total = result_df[class_name].sum()
                    totals_by_class[class_name] = class_total
                    grand_total += class_total
                totals_by_class["ИТОГО по категории"] = grand_total
                result_df = pd.concat([result_df, pd.DataFrame([totals_by_class])], ignore_index=True)
                
                result_df.to_excel(writer, sheet_name="Надомное отделение", index=False, startrow=3)
                
                worksheet = writer.sheets["Надомное отделение"]
                
                worksheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(classes)+2)
                worksheet.cell(row=1, column=1, value=sheet_title)
                worksheet.cell(row=1, column=1).font = Font(size=14, bold=True)
                worksheet.cell(row=1, column=1).alignment = Alignment(horizontal='center')
                
                for col, class_name in enumerate(classes, 2):
                    cell = worksheet.cell(row=3, column=col, value=class_name)
                    cell.font = Font(bold=True)
                    cell.alignment = Alignment(horizontal='center')
                
                cell = worksheet.cell(row=3, column=len(classes)+2, value="ИТОГО по категории")
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal='center')
                worksheet.cell(row=3, column=1, value="Категория")
                worksheet.cell(row=3, column=1).font = Font(bold=True)
                worksheet.cell(row=3, column=1).alignment = Alignment(horizontal='center')
                
                max_row = worksheet.max_row
                max_col = len(classes) + 2
                for row in range(1, max_row + 1):
                    for col in range(1, max_col + 1):
                        cell = worksheet.cell(row=row, column=col)
                        cell.border = thin_border
                        if row >= 3:
                            cell.alignment = Alignment(horizontal='center', vertical='center')
                    if row >= 4:
                        worksheet.cell(row=row, column=1).alignment = Alignment(horizontal='left', vertical='center')
                
                for col in range(1, max_col + 1):
                    max_length = 0
                    for row in range(1, max_row + 1):
                        cell_value = worksheet.cell(row=row, column=col).value
                        if cell_value:
                            max_length = max(max_length, len(str(cell_value)))
                    adjusted_width = min(max_length + 2, 35)
                    worksheet.column_dimensions[get_column_letter(col)].width = adjusted_width
                worksheet.column_dimensions['A'].width = 30
        
        # ========== ЛИСТ ДЛЯ ПРОДЛЕНКИ (для текущего здания) ==========
        # ИСПРАВЛЕНО: берем заявки на продленку для текущего здания
        after_school_df = get_after_school_requests(building, date_from, date_to)
        
        if not after_school_df.empty:
            by_date = {}
            for _, row in after_school_df.iterrows():
                date = row['date']
                class_name = row['class_name']
                quantity = row['quantity']
                if date not in by_date:
                    by_date[date] = {}
                by_date[date][class_name] = quantity
            
            data = []
            all_classes = set()
            for date, classes in by_date.items():
                all_classes.update(classes.keys())
            all_classes = sorted(all_classes)
            
            for date, classes in sorted(by_date.items()):
                date_display = datetime.strptime(date, "%Y-%m-%d").strftime("%d.%m.%Y")
                row = {"Дата": date_display}
                for class_name in all_classes:
                    row[class_name] = classes.get(class_name, 0)
                row["ИТОГО за день"] = sum(classes.values())
                data.append(row)
            
            result_df = pd.DataFrame(data)
            
            totals_row = {"Дата": "ВСЕГО"}
            for class_name in all_classes:
                totals_row[class_name] = result_df[class_name].sum()
            totals_row["ИТОГО за день"] = result_df["ИТОГО за день"].sum()
            result_df = pd.concat([result_df, pd.DataFrame([totals_row])], ignore_index=True)
            
            sheet_name = f"Продленка ({building})"
            result_df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=3)
            
            worksheet = writer.sheets[sheet_name]
            
            worksheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(all_classes)+2)
            worksheet.cell(row=1, column=1, value=f"Продленка ({building}) - {sheet_title}")
            worksheet.cell(row=1, column=1).font = Font(size=14, bold=True)
            worksheet.cell(row=1, column=1).alignment = Alignment(horizontal='center')
            
            for col, class_name in enumerate(all_classes, 2):
                cell = worksheet.cell(row=3, column=col, value=class_name)
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal='center')
            
            cell = worksheet.cell(row=3, column=len(all_classes)+2, value="ИТОГО за день")
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
            worksheet.cell(row=3, column=1, value="Дата")
            worksheet.cell(row=3, column=1).font = Font(bold=True)
            worksheet.cell(row=3, column=1).alignment = Alignment(horizontal='center')
            
            max_row = worksheet.max_row
            max_col = len(all_classes) + 2
            for row in range(1, max_row + 1):
                for col in range(1, max_col + 1):
                    cell = worksheet.cell(row=row, column=col)
                    cell.border = thin_border
                    if row >= 3:
                        cell.alignment = Alignment(horizontal='center', vertical='center')
                if row >= 4:
                    worksheet.cell(row=row, column=1).alignment = Alignment(horizontal='left', vertical='center')
            
            for col in range(1, max_col + 1):
                max_length = 0
                for row in range(1, max_row + 1):
                    cell_value = worksheet.cell(row=row, column=col).value
                    if cell_value:
                        max_length = max(max_length, len(str(cell_value)))
                adjusted_width = min(max_length + 2, 25)
                worksheet.column_dimensions[get_column_letter(col)].width = adjusted_width
    
    print(f"✅ Отчёт создан: {os.path.abspath(filename)}")
    
    try:
        from email_sender import send_report_via_email
        send_report_via_email(filename, period_type, building)
        print(f"📧 Отчёт отправлен на email")
    except Exception as e:
        print(f"❌ Ошибка отправки email: {e}")
    
    return filename
