from __future__ import annotations

import json

from sqlalchemy.orm import Session

from ..models import ImportRecord
from ..schemas.import_analysis import ResolutionReportResponse


class ImportAnalysisService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def save_analysis(self, report: ResolutionReportResponse, analyzed_by: str) -> ImportRecord:
        data = json.dumps({
            "source_name": report.source_name,
            "needed_libraries": report.needed_libraries,
            "resolved_count": report.resolved_count,
            "unresolved_count": report.unresolved_count,
            "missing_module_count": report.missing_module_count,
            "coverage": report.coverage,
            "score": report.score,
            "blockers": report.blockers,
            "imports_count": len(report.imports),
        })
        r = ImportRecord(title_name=report.source_name, status="complete", analyzed_by=analyzed_by, analysis_result=data)
        self.db.add(r)
        self.db.flush()
        return r

    def delete_analysis(self, analysis_id: int) -> bool:
        r = self.db.get(ImportRecord, analysis_id)
        if not r: return False
        self.db.delete(r)
        return True