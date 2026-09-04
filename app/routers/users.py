from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.location import LocationUpdate
from app.schemas.availability import AvailabilityUpdate
from app.core.dependencies import get_current_user


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


# ============================================================
# UPDATE CURRENT USER LOCATION
# RESPONDER ONLY
# ============================================================

@router.put(
    "/me/location",
    status_code=status.HTTP_200_OK
)
def update_my_location(
    location: LocationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    if current_user.role != "RESPONDER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only responders can update their location"
        )

    current_user.latitude = location.latitude
    current_user.longitude = location.longitude

    db.commit()
    db.refresh(current_user)

    return {
        "message": "Location updated successfully",
        "user_id": current_user.id,
        "latitude": current_user.latitude,
        "longitude": current_user.longitude
    }


# ============================================================
# UPDATE CURRENT USER AVAILABILITY
# RESPONDER ONLY
# ============================================================

@router.put(
    "/me/availability",
    status_code=status.HTTP_200_OK
)
def update_my_availability(
    availability: AvailabilityUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # 1. Only responders can change responder availability
    # --------------------------------------------------------

    if current_user.role != "RESPONDER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only responders can update availability"
        )

    # --------------------------------------------------------
    # 2. Prevent responder from going offline while busy
    # --------------------------------------------------------

    if (
        current_user.availability_status == "BUSY"
        and availability.availability_status == "OFFLINE"
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Busy responder cannot go offline"
        )

    # --------------------------------------------------------
    # 3. Update availability
    # --------------------------------------------------------

    current_user.availability_status = (
        availability.availability_status
    )

    # --------------------------------------------------------
    # 4. Save changes
    # --------------------------------------------------------

    db.commit()
    db.refresh(current_user)

    return {
        "message": "Availability updated successfully",
        "user_id": current_user.id,
        "availability_status": current_user.availability_status
    }
