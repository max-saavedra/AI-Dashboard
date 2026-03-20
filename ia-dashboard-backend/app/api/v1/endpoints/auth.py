"""
app/api/v1/endpoints/auth.py

Authentication endpoints that integrate with Supabase Auth.
- POST /api/v1/auth/login  – authenticate with email and password, return JWT
- POST /api/v1/auth/signup – create a new user account
- POST /api/v1/auth/refresh – refresh expired access token
- POST /api/v1/auth/migrate-temporary-data – migrate anon dashboards to permanent storage
"""

import uuid as uuid_lib
from pydantic import BaseModel, EmailStr, Field
from fastapi import APIRouter, HTTPException, status, Depends
from supabase import create_client, Client
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.dependencies import optional_current_user
from app.core.security import TokenPayload
from app.models.database import User
from app.models.session import get_db

router = APIRouter()
logger = get_logger(__name__)
settings = get_settings()

# Initialize Supabase client
supabase: Client = create_client(
    settings.supabase_url,
    settings.supabase_anon_key
)


class LoginRequest(BaseModel):
    """Login request with email and password."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="User password")


class SignupRequest(BaseModel):
    """Signup request with email and password."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="User password")


class RefreshRequest(BaseModel):
    """Refresh token request."""

    refresh_token: str = Field(..., description="Refresh token")


class AuthResponse(BaseModel):
    """Authentication response containing JWT token."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(
        ..., description="Refresh token for obtaining new JWT"
    )
    token_type: str = Field(default="bearer", description="Token type")
    user_id: str = Field(..., description="User UUID")
    email: str = Field(..., description="User email address")


def _extract_error_message(exc: Exception) -> tuple[str, int]:
    """Extract error message and status code from Supabase exceptions."""
    error_str = str(exc).lower()
    exc_type = type(exc).__name__

    logger.info(
        "DEBUG: Extracting error info",
        exception_type=exc_type,
        exception_message=str(exc)[:200],
    )

    # Check for specific error patterns
    if "user already exists" in error_str or "email already registered" in error_str:
        logger.warning("DEBUG: Email already registered error detected")
        return "email_already_registered", status.HTTP_409_CONFLICT

    if "invalid password" in error_str or "weak password" in error_str:
        logger.warning("DEBUG: Weak password error detected")
        return "weak_password", status.HTTP_400_BAD_REQUEST

    if "invalid email" in error_str:
        logger.warning("DEBUG: Invalid email error detected")
        return "invalid_email", status.HTTP_400_BAD_REQUEST

    if "invalid credentials" in error_str or "invalid login" in error_str:
        logger.warning("DEBUG: Invalid credentials error detected")
        return "invalid_credentials", status.HTTP_401_UNAUTHORIZED

    if "timeout" in error_str:
        logger.warning("DEBUG: Timeout error detected")
        return "timeout", status.HTTP_504_GATEWAY_TIMEOUT

    logger.warning("DEBUG: Generic error detected", exc_type=exc_type)
    return "auth_error", status.HTTP_400_BAD_REQUEST


async def _ensure_local_user(
    user_id: str, email: str, db: AsyncSession
) -> User:
    """
    Ensure a user exists in the local users table.
    If not, create it. If it exists, return it.
    """
    try:
        # Convert string UUID to UUID object
        user_uuid = uuid_lib.UUID(user_id)

        # Check if user exists
        stmt = select(User).where(User.id == user_uuid)
        result = await db.execute(stmt)
        user = result.scalars().first()

        if user:
            logger.info(
                "DEBUG: User already exists in local database",
                user_id=user_id,
                email=email,
            )
            return user

        # Create new user in local database
        logger.info(
            "DEBUG: Creating user in local database",
            user_id=user_id,
            email=email,
        )
        new_user = User(id=user_uuid, email=email)
        db.add(new_user)
        await db.flush()

        logger.info(
            "DEBUG: User created in local database",
            user_id=user_id,
            email=email,
        )
        return new_user

    except Exception as exc:
        logger.warning(
            "DEBUG: Failed to ensure local user",
            user_id=user_id,
            email=email,
            error=str(exc),
        )
        raise


@router.post(
    "/auth/login",
    response_model=AuthResponse,
    summary="Authenticate user with email and password",
    status_code=status.HTTP_200_OK,
)
async def login(
    request: LoginRequest, db: AsyncSession = Depends(get_db)
) -> AuthResponse:
    """
    Authenticate a user with email and password.
    Returns a JWT token that the frontend can use for subsequent requests.
    Also ensures user exists in local database.
    """
    logger.info("DEBUG: Login attempt started", email=request.email)

    try:
        logger.info(
            "DEBUG: Calling Supabase sign_in_with_password",
            email=request.email,
        )

        # Call Supabase Auth
        response = supabase.auth.sign_in_with_password(
            {
                "email": request.email,
                "password": request.password,
            }
        )

        user = response.user
        session = response.session

        if user is None:
            logger.warning("DEBUG: Login response has no user")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if session is None:
            logger.warning("DEBUG: Login response has no session")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Ensure user exists in local database
        logger.info("DEBUG: Ensuring user exists in local database")
        try:
            await _ensure_local_user(user.id, user.email, db)
            await db.commit()
            logger.info("DEBUG: User ensured in local database")
        except Exception as exc:
            logger.warning(
                "DEBUG: Failed to ensure user in local database",
                error=str(exc),
            )
            await db.rollback()
            # Continue anyway - auth was successful

        logger.info(
            "DEBUG: Login successful",
            user_id=user.id,
            email=user.email,
            token_length=len(session.access_token)
            if session.access_token
            else 0,
        )

        return AuthResponse(
            access_token=session.access_token,
            refresh_token=session.refresh_token,
            token_type="bearer",
            user_id=user.id,
            email=user.email,
        )

    except HTTPException:
        raise
    except Exception as exc:
        error_msg, status_code = _extract_error_message(exc)

        logger.warning(
            "DEBUG: Login failed",
            email=request.email,
            error_code=error_msg,
            error_type=type(exc).__name__,
        )

        detail_map = {
            "invalid_credentials": "Invalid email or password",
            "email_already_registered": "Email already registered",
            "weak_password": "Password is too weak",
            "invalid_email": "Invalid email format",
            "timeout": "Request timeout - Supabase server not responding",
            "auth_error": "Authentication failed",
        }

        raise HTTPException(
            status_code=status_code,
            detail=detail_map.get(error_msg, str(exc)),
        )


@router.post(
    "/auth/signup",
    response_model=AuthResponse,
    summary="Create a new user account",
    status_code=status.HTTP_201_CREATED,
)
async def signup(
    request: SignupRequest, db: AsyncSession = Depends(get_db)
) -> AuthResponse:
    """
    Create a new user account with email and password.
    Automatically signs in the new user and returns a JWT token.
    Also creates user record in local database.
    """
    logger.info("DEBUG: Signup attempt started", email=request.email)

    try:
        logger.info("DEBUG: Calling Supabase sign_up", email=request.email)

        # Create user account with Supabase Auth
        response = supabase.auth.sign_up(
            {
                "email": request.email,
                "password": request.password,
            }
        )

        user = response.user
        session = response.session

        logger.info(
            "DEBUG: Supabase sign_up response received",
            has_user=user is not None,
            has_session=session is not None,
            user_id=user.id if user else None,
        )

        if user is None:
            logger.warning("DEBUG: Signup response has no user")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create account",
            )

        # Create user in local database
        logger.info("DEBUG: Creating user in local database")
        try:
            await _ensure_local_user(user.id, user.email, db)
            await db.commit()
            logger.info("DEBUG: User created in local database successfully")
        except Exception as exc:
            logger.warning(
                "DEBUG: Failed to create user in local database",
                error=str(exc),
            )
            await db.rollback()
            # Note: We don't stop here because user is already in Supabase

        # If no session, email confirmation is required
        if session is None:
            logger.info(
                "DEBUG: Email confirmation required",
                user_id=user.id,
                email=user.email,
            )
            raise HTTPException(
                status_code=status.HTTP_202_ACCEPTED,
                detail="Account created. Please check your email to confirm.",
            )

        logger.info(
            "DEBUG: Signup and auto-signin successful",
            user_id=user.id,
            email=user.email,
            token_length=len(session.access_token)
            if session.access_token
            else 0,
        )

        return AuthResponse(
            access_token=session.access_token,
            refresh_token=session.refresh_token,
            token_type="bearer",
            user_id=user.id,
            email=user.email,
        )

    except HTTPException:
        raise
    except Exception as exc:
        error_msg, status_code = _extract_error_message(exc)

        logger.warning(
            "DEBUG: Signup failed",
            email=request.email,
            error_code=error_msg,
            error_type=type(exc).__name__,
        )

        detail_map = {
            "email_already_registered": "This email is already registered",
            "weak_password": "Password must be at least 6 characters",
            "invalid_email": "Invalid email format",
            "timeout": "Request timeout - Supabase server not responding",
            "auth_error": "Failed to create account",
        }

        raise HTTPException(
            status_code=status_code,
            detail=detail_map.get(error_msg, "Failed to create account"),
        )


@router.post(
    "/auth/refresh",
    response_model=AuthResponse,
    summary="Refresh access token",
    status_code=status.HTTP_200_OK,
)
async def refresh(request: RefreshRequest) -> AuthResponse:
    """
    Obtain a new access token using a refresh token.
    """
    logger.info("DEBUG: Token refresh attempt started")

    if not request.refresh_token:
        logger.warning("DEBUG: Refresh token not provided")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token is required",
        )

    try:
        logger.info("DEBUG: Calling Supabase refresh_session")
        response = supabase.auth.refresh_session(request.refresh_token)

        user = response.user
        session = response.session

        if user is None or session is None:
            logger.warning("DEBUG: Refresh response missing user or session")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to refresh token",
            )

        logger.info(
            "DEBUG: Token refresh successful",
            user_id=user.id,
            email=user.email,
        )

        return AuthResponse(
            access_token=session.access_token,
            refresh_token=session.refresh_token,
            token_type="bearer",
            user_id=user.id,
            email=user.email,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.warning(
            "DEBUG: Token refresh failed",
            error_type=type(exc).__name__,
            error_message=str(exc)[:200],
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to refresh token. Please login again.",
        )


class MigrateTemporaryDataRequest(BaseModel):
    """Request to migrate temporary dashboard data to permanent storage."""

    session_id: str = Field(
        ...,
        description="The session ID from the temporary dashboard",
    )


class MigrateTemporaryDataResponse(BaseModel):
    """Response after migrating temporary data."""

    success: bool = Field(..., description="Whether migration was successful")
    message: str = Field(..., description="Detail message")
    migrated_count: int = Field(
        ..., description="Number of dashboards migrated"
    )


@router.post(
    "/auth/migrate-temporary-data",
    response_model=MigrateTemporaryDataResponse,
    summary="Migrate temporary dashboard data to permanent storage",
    status_code=status.HTTP_200_OK,
)
async def migrate_temporary_data(
    request: MigrateTemporaryDataRequest,
    current_user: TokenPayload = Depends(optional_current_user),
    db: AsyncSession = Depends(get_db),
) -> MigrateTemporaryDataResponse:
    """
    Migrate temporary dashboards (created by anonymous users) to permanent
    storage under the authenticated user's account.

    After signup, users can pass their session_id to save their anonymous
    analysis work to their account.
    """
    from app.models.database import TemporaryDashboard, Chat, Dashboard
    import uuid as _uuid

    logger.info(
        "DEBUG: Migrate temporary data requested",
        session_id=request.session_id,
        user_id=current_user.sub if current_user else None,
    )

    # Require authentication
    if not current_user or not current_user.sub:
        logger.warning("DEBUG: Migration attempt without authentication")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to migrate data.",
        )

    try:
        # Find all temporary dashboards for this session
        stmt = select(TemporaryDashboard).where(
            TemporaryDashboard.session_id == request.session_id
        )
        result = await db.execute(stmt)
        temp_dashboards = result.scalars().all()

        if not temp_dashboards:
            logger.info(
                "DEBUG: No temporary dashboards found for session",
                session_id=request.session_id,
            )
            return MigrateTemporaryDataResponse(
                success=True,
                message="No temporary data found for this session.",
                migrated_count=0,
            )

        # Create a chat for this user
        user_uuid = _uuid.UUID(current_user.sub)
        chat = Chat(
            id=_uuid.uuid4(),
            user_id=user_uuid,
            name="Migrated Analysis",
        )
        db.add(chat)
        await db.flush()

        # Migrate each temporary dashboard
        for temp_dash in temp_dashboards:
            perma_dash = Dashboard(
                id=temp_dash.id,
                chat_id=chat.id,
                cleaned_data=temp_dash.cleaned_data,
                kpi_data=temp_dash.kpi_data,
                ai_insights=temp_dash.ai_insights,
                chart_config=temp_dash.chart_config,
                analysis_metadata=temp_dash.analysis_metadata,
            )
            db.add(perma_dash)

        # Delete temporary dashboards
        for temp_dash in temp_dashboards:
            await db.delete(temp_dash)

        await db.commit()

        logger.info(
            "DEBUG: Temporary data migrated successfully",
            session_id=request.session_id,
            user_id=current_user.sub,
            count=len(temp_dashboards),
        )

        return MigrateTemporaryDataResponse(
            success=True,
            message=f"Successfully migrated {len(temp_dashboards)} dashboard(s).",
            migrated_count=len(temp_dashboards),
        )

    except Exception as exc:
        logger.error(
            "DEBUG: Migration failed",
            session_id=request.session_id,
            error=str(exc),
        )
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to migrate temporary data.",
        )
