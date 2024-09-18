import csv
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from .custom_exceptions import ExportError

class DataExporter:
    @staticmethod
    def export_to_csv(data, filename):
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(data[0].keys())  # Write header
                for row in data:
                    writer.writerow(row.values())
        except Exception as e:
            raise ExportError(f"Errore durante l'esportazione in CSV: {str(e)}")

    @staticmethod
    def export_to_pdf(data, filename, title, image_buffer=None):
        try:
            doc = SimpleDocTemplate(filename, pagesize=letter)
            elements = []

            styles = getSampleStyleSheet()
            elements.append(Paragraph(title, styles['Title']))

            if image_buffer:
                img = Image(image_buffer)
                img.drawHeight = 300
                img.drawWidth = 500
                elements.append(img)

            table_data = [list(data[0].keys())]  # Header
            for row in data:
                table_data.append(list(row.values()))

            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 12),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))

            elements.append(table)
            doc.build(elements)
        except Exception as e:
            raise ExportError(f"Errore durante l'esportazione in PDF: {str(e)}")

    @staticmethod
    def export_participant_performance(df, img_buffer, filename):
        try:
            DataExporter.export_to_csv(df.reset_index().to_dict('records'), filename + '.csv')
            DataExporter.export_to_pdf(df.reset_index().to_dict('records'), filename + '.pdf', 'Prestazioni dei Partecipanti', img_buffer)
        except Exception as e:
            raise ExportError(f"Errore durante l'esportazione delle prestazioni dei partecipanti: {str(e)}")

    @staticmethod
    def export_most_predicted_teams(series, img_buffer, filename):
        try:
            data = [{'Squadra': team, 'Numero di Pronostici': count} for team, count in series.items()]
            DataExporter.export_to_csv(data, filename + '.csv')
            DataExporter.export_to_pdf(data, filename + '.pdf', 'Squadre più Pronosticate', img_buffer)
        except Exception as e:
            raise ExportError(f"Errore durante l'esportazione delle squadre più pronosticate: {str(e)}")

    @staticmethod
    def export_weekly_prizes(df, img_buffer, filename):
        try:
            DataExporter.export_to_csv(df.to_dict('records'), filename + '.csv')
            DataExporter.export_to_pdf(df.to_dict('records'), filename + '.pdf', 'Premi Settimanali Assegnati', img_buffer)
        except Exception as e:
            raise ExportError(f"Errore durante l'esportazione dei premi settimanali: {str(e)}")

    @staticmethod
    def export_final_standings(df, img_buffer, filename):
        try:
            DataExporter.export_to_csv(df.to_dict('records'), filename + '.csv')
            DataExporter.export_to_pdf(df.to_dict('records'), filename + '.pdf', 'Classifica Finale del Torneo', img_buffer)
        except Exception as e:
            raise ExportError(f"Errore durante l'esportazione della classifica finale: {str(e)}")

    @staticmethod
    def export_tournament_summary(summary, filename):
        try:
            DataExporter.export_to_csv([summary], filename + '.csv')
            DataExporter.export_to_pdf([summary], filename + '.pdf', 'Riepilogo del Torneo')
        except Exception as e:
            raise ExportError(f"Errore durante l'esportazione del riepilogo del torneo: {str(e)}")