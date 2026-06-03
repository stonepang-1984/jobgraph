"""简历相关 API 端点"""

import tempfile
import os
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel, Field

from src.jobgraph.resume import resume_parser, resume_extractor, privacy_filter
from src.jobgraph.matching import job_matcher
from src.jobgraph.graph_manager import job_manager
from src.jobgraph.models import UserProfile

router = APIRouter(prefix="/api/resume", tags=["resume"])


class ResumeUploadResponse(BaseModel):
    """简历上传响应"""
    success: bool
    message: str
    profile: dict | None = None
    privacy_filtered: list[str] = []


class MatchRequest(BaseModel):
    """匹配请求"""
    user_id: str | None = None
    job_title: str | None = None
    skills: list[str] | None = None
    experience_years: int | None = None
    education: str | None = None
    location: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    prefer_remote: bool = False
    limit: int = 20


class MatchResponse(BaseModel):
    """匹配响应"""
    success: bool
    matches: list[dict]
    total_count: int
    need_manual_input: bool = False
    message: str = ""


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(file: UploadFile = File(...)):
    """上传并解析简历

    支持 PDF、DOCX 格式
    自动过滤隐私信息
    """
    # 检查文件类型
    ext = Path(file.filename).suffix.lower()
    if ext not in [".pdf", ".docx"]:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {ext}，支持: .pdf, .docx"
        )

    # 保存上传文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # 解析简历
        text = resume_parser.parse(tmp_path)

        # 扫描隐私信息
        privacy_scan = privacy_filter.scan(text)
        filtered_types = list(privacy_scan.keys())

        # 过滤隐私信息
        filtered_text = privacy_filter.filter(text)

        # 提取信息
        profile = resume_extractor.extract(filtered_text)

        return ResumeUploadResponse(
            success=True,
            message="简历解析成功",
            profile={
                "current_title": profile.current_title,
                "experience_years": profile.experience_years,
                "education": profile.education,
                "skills": profile.skills,
                "certifications": profile.certifications,
                "work_history": profile.work_history,
                "projects": profile.projects,
            },
            privacy_filtered=filtered_types,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"简历解析失败: {str(e)}")

    finally:
        # 清理临时文件
        os.unlink(tmp_path)


@router.post("/match/by-resume", response_model=MatchResponse)
async def match_by_resume(request: MatchRequest):
    """基于简历信息匹配岗位

    需要先上传简历获取 profile，然后调用此接口进行匹配
    """
    try:
        # 创建用户档案
        import hashlib
        user_id = request.user_id or hashlib.md5(
            "resume_user".encode()
        ).hexdigest()[:16]

        user = UserProfile(
            id=user_id,
            current_title=request.job_title,
            experience_years=request.experience_years or 0,
            education=request.education,
            skills=request.skills or [],
            desired_salary_min=request.salary_min,
            desired_salary_max=request.salary_max,
            desired_locations=[request.location] if request.location else [],
            prefer_remote=request.prefer_remote,
        )

        # 保存用户档案
        job_manager.create_user_profile(user)

        # 执行匹配
        result = job_matcher.match_by_profile(user_id, limit=request.limit)

        return MatchResponse(
            success=True,
            matches=result.matches,
            total_count=result.total_count,
            need_manual_input=result.need_manual_input,
            message=result.message,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"匹配失败: {str(e)}")


@router.post("/match/by-manual", response_model=MatchResponse)
async def match_by_manual(request: MatchRequest):
    """基于手动输入匹配岗位"""
    try:
        result = job_matcher.match_by_manual_input(
            job_title=request.job_title,
            skills=request.skills,
            experience_years=request.experience_years,
            education=request.education,
            location=request.location,
            salary_min=request.salary_min,
            salary_max=request.salary_max,
            limit=request.limit,
        )

        return MatchResponse(
            success=True,
            matches=result.matches,
            total_count=result.total_count,
            need_manual_input=False,
            message=result.message,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"匹配失败: {str(e)}")


@router.post("/scan-privacy")
async def scan_privacy(file: UploadFile = File(...)):
    """扫描简历中的隐私信息（不修改文件）

    返回检测到的隐私信息类型和数量
    """
    # 检查文件类型
    ext = Path(file.filename).suffix.lower()
    if ext not in [".pdf", ".docx"]:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {ext}，支持: .pdf, .docx"
        )

    # 保存上传文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # 解析简历
        text = resume_parser.parse(tmp_path)

        # 扫描隐私信息
        scan_result = privacy_filter.scan(text)

        return {
            "success": True,
            "has_privacy": len(scan_result) > 0,
            "privacy_info": scan_result,
            "message": f"检测到 {sum(scan_result.values())} 处隐私信息" if scan_result else "未检测到隐私信息",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"扫描失败: {str(e)}")

    finally:
        # 清理临时文件
        os.unlink(tmp_path)
