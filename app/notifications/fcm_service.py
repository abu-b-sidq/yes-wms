from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("app.notifications.fcm")


def send_push(user_id: str, title: str, body: str, data: dict[str, Any] | None = None) -> None:
    """Send FCM push notification to all active devices for a user."""
    try:
        import firebase_admin
        from firebase_admin import messaging
    except ImportError:
        logger.warning("firebase-admin not installed, skipping push notification")
        return

    from app.notifications.models import DeviceToken

    tokens = list(
        DeviceToken.objects.filter(
            user_id=user_id,
            is_active=True,
        ).values_list("token", flat=True)
    )

    if not tokens:
        return

    message_data = {str(k): str(v) for k, v in (data or {}).items()}

    for token in tokens:
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=message_data,
                token=token,
                android=messaging.AndroidConfig(
                    priority="high",
                    notification=messaging.AndroidNotification(
                        sound="default",
                        channel_id="wms_tasks",
                    ),
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound="default",
                            badge=1,
                        ),
                    ),
                ),
            )
            messaging.send(message)
        except messaging.UnregisteredError:
            # Token is no longer valid
            DeviceToken.objects.filter(token=token).update(is_active=False)
            logger.info("Deactivated unregistered FCM token for user %s", user_id)
        except Exception as e:
            logger.warning("Failed to send FCM to user %s: %s", user_id, e)


def notify_new_pick_task(facility_id: str, pick) -> None:
    """Notify all workers in a facility about a new available pick task."""
    from app.notifications.models import DeviceToken

    # Get all active device tokens for this facility
    tokens = list(
        DeviceToken.objects.filter(
            facility_id=facility_id,
            is_active=True,
        ).select_related("user")
    )

    for device in tokens:
        send_push(
            user_id=str(device.user_id),
            title="New Pick Task Available",
            body=f"Pick {pick.sku.code} x {pick.quantity} from {pick.source_entity_code}",
            data={
                "type": "new_pick_task",
                "pick_id": str(pick.pk),
                "sku_code": pick.sku.code,
            },
        )


def notify_drop_assigned(user, drop) -> None:
    """Notify a worker that a drop task has been assigned to them."""
    send_push(
        user_id=str(user.pk),
        title="Drop Task Assigned",
        body=f"Drop {drop.sku.code} x {drop.quantity} to {drop.dest_entity_code}",
        data={
            "type": "drop_assigned",
            "drop_id": str(drop.pk),
            "sku_code": drop.sku.code,
        },
    )
