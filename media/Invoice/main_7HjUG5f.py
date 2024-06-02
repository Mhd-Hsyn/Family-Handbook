import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, HTTPException, Depends, Body
from fastapi_sqlalchemy import DBSessionMiddleware
from sqlalchemy.orm import Session
from Database.database import *
from p2p_webapi.models.schema import *
from Database.models import *
from p2p_webapi.core.utils import *
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from decouple import config
from sqlalchemy.future import select
from passlib.context import CryptContext
import uvicorn
import p2p_webapi.core.emailpattern as verfied
from p2p_webapi.core.emailpattern import *
import random
import stripe
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import logging


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

dev_logger = logging.getLogger("dev_logger")
dev_logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    "%(asctime)s  | %(levelname)s | %(filename)s | %(message)s"
)
handler = logging.StreamHandler()
handler.setFormatter(formatter)

dev_logger.addHandler(handler)
logger = logging.getLogger("dev_logger")

app.add_middleware(DBSessionMiddleware, db_url=DATABASE_URL)

handler = CryptContext(schemes=["bcrypt"], deprecated="auto")


@app.post("/signup", response_model=dict)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    try:
        if not email_unique(user.email, db):
            raise HTTPException(status_code=400, detail="Email already registered")

        if not valid_password(user.password):
            raise HTTPException(
                status_code=400, detail="Password must be 8 to 20 characters long"
            )
        
        hashed_password = handler.hash(user.password)

        singup_otp = generate_otp()

        user_db = User(
            fname=user.fname,
            lname=user.lname,
            username=user.username,
            email=user.email,
            password=hashed_password,
            singup_otp=singup_otp,
        )


        send_email_with_otp_singup(user.email, singup_otp)

        db.add(user_db)
        db.commit()
        db.refresh(user_db)
        
        response_user = {
            "fname": user_db.fname,
            "lname": user_db.lname,
            "username": user_db.username,
            "email": user_db.email,
        }
        logger.info("User signup otp send successfully")
        return {
            "status": True,
            "detail": "Check Your Email & Verify OTP",
            "data": response_user,
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        print("Exception:", e)
        raise HTTPException(status_code=500, detail="Error creating user {e}")


@app.post("/verify_signup_otp", response_model=dict)
async def create_user(user: VerifyOtp, db: Session = Depends(get_db)):
    try:
        user_db = db.query(User).filter(User.email == user.email).first()

        if user_db is None:
            raise HTTPException(status_code=404, detail="User not found")

        if user_db.singup_otp != user.singup_otp:
            raise HTTPException(status_code=400, detail="Invalid signup OTP")

        user_db.singup_otp = 0
        db.commit()

        response_user = {
            "id": user_db.id,
            "fname": user_db.fname,
            "lname": user_db.lname,
            "username": user_db.username,
            "email": user_db.email,
        }
        logger.info("User signup otp verify successfully")
        return {
            "status": True,
            "detail": "Signup Successfully",
            "data": response_user,
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        print("Exception:", e)
        raise HTTPException(status_code=500, detail="Error creating user")


@app.post("/login")
async def login(
    request: Request, login_request: LoginRequest, db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == login_request.email).first()
    if user:
        if user.singup_otp == 0 and handler.verify(login_request.password, user.password):
            otp = generate_otp()

            user.login_otp = otp
            db.commit()

            send_email_with_otp_login(user.email, otp)

            user_response = {
                "id": str(user.id),
                "email": user.email,
            }
            logger.info("User login otp send successfully")
            return JSONResponse(
                content={
                    "status": True,
                    "detail": "OTP sent to your email",
                    "data": user_response,
                }
            )
        else:
            raise HTTPException(status_code=403, detail="User not verified yet")
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")


@app.post("/verify_login_otp")
async def login(
    request: Request, login_request: VerifyLoginRequest, db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == login_request.email).first()
    if user and user.login_otp == login_request.login_otp:
        token = generate_token(user.id, user.email)
        user_response = {"id": str(user.id), "email": user.email}

        whitelisttoken_id = str(uuid.uuid4())

        whitelist_token = Whitelisttoken(
            email=user.email, token=token, id=whitelisttoken_id
        )

        db.add(whitelist_token)
        db.commit()

        stripe_detail = (
            db.query(Stripedetails).filter(Stripedetails.email == user.email).first()
        )

        stripe_id = ""

        if stripe_detail:
            stripe_id = stripe_detail.stripe_id

        user_response["stripe_id"] = stripe_id
        logger.info("User login otp verify successfully")
        return JSONResponse(
            content={
                "status": True,
                "detail": "Login Successfully",
                "token": token,
                "data": user_response,
            }
        )
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")


@app.post("/forget_pass_send_mail")
async def forget_pass_send_mail(
    request: Request,
    forget_pass_request: ForgetPassRequest,
    db: Session = Depends(get_db),
):
    try:
        email = forget_pass_request.email

        query = select(User).filter(User.email == email)
        fetch_user = db.execute(query)
        user = fetch_user.scalar()

        if user:
            token = random.randrange(100000, 999999, 6)
            user.otp = token
            user.otp_count = 0
            user.otp_status = True
            db.commit()
            emailstatus = verfied.forgetEmailPattern(
                {
                    "subject": "forget password",
                    "EMAIL_HOST_USER": config("EMAIL_USERNAME"),
                    "toemail": email,
                    "token": token,
                }
            )
            logger.info("Forget Password email send successfully")
            if emailstatus:
                return {
                    "status": True,
                    "detail": "Email send successfully",
                    "id": user.id,
                }
            else:
                return {"status": False, "detail": "Something went wrong"}
        else:
            raise HTTPException(status_code=404, detail="Email does not exist")

    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/check_otp", response_model=dict)
async def check_otp(request: OtpCheckRequest, db: Session = Depends(get_db)):
    try:
        fetchuser = db.query(User).filter(User.id == request.id).first()

        if fetchuser:
            if fetchuser.otp_status and fetchuser.otp_count < 3:
                if fetchuser.otp == request.otp:
                    fetchuser.otp = 0
                    db.commit()
                    logger.info("Forget Password Otp verified successfully")
                    return {
                        "status": True,
                        "detail": "Otp verified",
                        "id": str(fetchuser.id),
                    }
                else:
                    fetchuser.otp_count += 1
                    db.commit()
                    fetchuser.otp = 0
                    fetchuser.otp_count = 0
                    fetchuser.otp_status = False
                    db.commit()
                    return {
                        "status": False,
                        "detail": "Your OTP is expired. Kindly get OTP again",
                    }

            return {
                "status": False,
                "detail": "Your OTP is expired. Kindly get OTP again",
            }
        return {"status": False, "detail": "User not exist"}, 404
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/reset_password")
async def reset_password(
    request_data: ResetPasswordRequest, db: Session = Depends(get_db)
):
    try:
        uid = request_data.id
        newpassword = request_data.newpassword

        fetchuser = db.query(User).filter(User.id == uid).first()

        if not fetchuser:
            raise HTTPException(status_code=404, detail="User Not Exist")

        if not valid_password(newpassword):
            raise HTTPException(
                status_code=400,
                detail="Password length must be greater than 8",
            )

        if fetchuser.otp_status == True and fetchuser.otp == 0:
            fetchuser.password = handler.hash(newpassword)
            fetchuser.otp_status = False
            fetchuser.otp_count = 0
            db.commit()
            logger.info("Forget Password Successfully")
            return {"status": True, "detail": "Forget Password Successfully"}

        raise HTTPException(status_code=400, detail="Token not verified")

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/create_stripe_account/")
async def create_stripe_account(
    request_data: StripeAccountCreateRequest, db: Session = Depends(get_db),
    user: dict = Depends(authenticate_user),
):
    email = request_data.email

    stripe.api_key = config("STRIPE_SECRET_KEY")

    all_accounts = stripe.Account.auto_paging_iter()
    existing_account = next(
        (account for account in all_accounts if account.email == email), None
    )
    if existing_account:
        raise HTTPException(
            status_code=400,
            detail=f"Already have an account with this email '{email}'.",
        )

    account = stripe.Account.create(
    type="custom",
    country="US",
    email=email,
    capabilities={
        "card_payments": {"requested": True},
        "transfers": {"requested": True},
        }
    )

    user_id = account.id
    print("user_id", user_id)

    stripe_account_data = {
        "stripe_id": account.id,
        "email": account.email,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }

    stripedetail = Stripedetails(**stripe_account_data)
    db.add(stripedetail)
    db.commit()
    logger.info("Stripe Account Created Successfully")
    return {
        "status": True,
        "detail": "Stripe account created successfully",
        "stripe_account": account.id,
        "email": email,
        "stripe_account_data": stripe_account_data,
    }


@app.post("/connect_to_connect_account/")
async def connect_to_connect_account(
    request_data: ConnectAccountRequest,
    user: dict = Depends(authenticate_user),
):
    try:
        stripe.api_key = config("STRIPE_SECRET_KEY")

        all_accounts = stripe.Account.auto_paging_iter()
        existing_account = next(
            (account for account in all_accounts if account.id == request_data.account),
            None,
        )

        if existing_account:
            if existing_account.details_submitted:
                raise HTTPException(
                    status_code=400, detail="You are already connected to this account."
                )
            else:
                account_link = stripe.AccountLink.create(
                    account=request_data.account,
                    refresh_url="https://www.example.com/refresh",
                    return_url="https://www.example.com/return",
                    type="account_onboarding",
                )

                email_response = send_email(existing_account.email, account_link.url)
                logger.info("Stripe To Connect Link send Successfully")
                return {
                    "status": True,
                    "detail": "Check Your Email & Visit Link",
                    "email": existing_account.email,
                    "link": account_link.url,
                    "created_at": datetime.now().isoformat(),
                }

        else:
            raise HTTPException(status_code=404, detail="Account not found.")

    except stripe.error.StripeError as e:
        return {"error": str(e)}


@app.get("/get_wallet_balance/{user_id}")
async def get_wallet_balance(
    user_id: str,
    user: dict = Depends(authenticate_user),
):
    try:
        stripe.api_key = config("STRIPE_SECRET_KEY")

        balance = stripe.Balance.retrieve(stripe_account=user_id)
        logger.info("Wallet  Balance Get Successfully")
        return {"wallet_balance": balance.available[0].amount / 100}

    except stripe.error.StripeError as e:
        return {"error": str(e)}


@app.get("/get_account")
async def get_stripe_id(email_request: EmailRequest, db: Session = Depends(get_db)):
    stripedetails = (
        db.query(Stripedetails)
        .filter(Stripedetails.email == email_request.email)
        .first()
    )
    if stripedetails is None:
        raise HTTPException(
            status_code=404, detail="Stripe details not found for the given email"
        )
    logger.info("Stripe Account Get Successfully")
    return {"stripe_id": stripedetails.stripe_id, "email": stripedetails.email}


@app.get("/get_stripe_account", response_model=List[EmailRequest])
async def get_stripe_accounts(db: Session = Depends(get_db),
    user: dict = Depends(authenticate_user),):
    stripedetails = db.query(Stripedetails).all()
    if not stripedetails:
        raise HTTPException(status_code=404, detail="No Stripe details found")
    return stripedetails


@app.post("/transfer_payment")
async def transfer_payment(
    transfer_request: TransferRequest, db: Session = Depends(get_db),
    user: dict = Depends(authenticate_user),
):
    try:
        stripe.api_key = config("STRIPE_SECRET_KEY")
        amount_in_cents = int(float(transfer_request.amount) * 100)

        user_stripe_details = (
            db.query(Stripedetails)
            .filter(Stripedetails.email == transfer_request.from_email)
            .first()
        )
        if not user_stripe_details:
            raise HTTPException(
                status_code=404, detail="Stripe details not found for the user"
            )

        user_balance = stripe.Balance.retrieve(
            stripe_account=user_stripe_details.stripe_id
        )
        available_balance = user_balance.available[0].amount
        print(available_balance)

        transfer = stripe.Transfer.create(
            amount=amount_in_cents,
            currency="usd",
            destination=transfer_request.destination,
            description="Transfer to connected account",
        )
        print("Transfer ID:", transfer.id)

        transfer_record = Paymentdetail(
            from_email=transfer_request.from_email,
            from_stripe_id=transfer_request.from_stripe_id,
            to_email=transfer_request.to_email,
            to_stripe_id=transfer_request.destination,
            amount=float(transfer_request.amount),
            currency="usd",
        )
        db.add(transfer_record)
        db.commit()
        logger.info("Payment Transfer Successfully")
        return {"detail": "Transfer successful", "transfer_id": transfer.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/get_payment_history/{email}")
async def get_payment_details(email: str, db: Session = Depends(get_db),
    user: dict = Depends(authenticate_user),):
    payments_sent = (
        db.query(Paymentdetail)
        .filter(Paymentdetail.from_email == email)
        .order_by(
            Paymentdetail.created_at.desc()
        )
        .all()
    )
    payments_received = (
        db.query(Paymentdetail)
        .filter(Paymentdetail.to_email == email)
        .order_by(
            Paymentdetail.created_at.desc()
        )
        .all()
    )

    sent_payments_data = [
        {
            "to_email": payment.to_email,
            "amount": payment.amount,
            "created_at": payment.created_at,
        }
        for payment in payments_sent
    ]
    received_payments_data = [
        {
            "from_email": payment.from_email,
            "amount": payment.amount,
            "created_at": payment.created_at,
        }
        for payment in payments_received
    ]
    logger.info("Payment History Get Successfully")
    
    return {
        "transfer_payments": sent_payments_data,
        "received_payments": received_payments_data,
    }


@app.get("/get_payment/{email}")
async def get_payment_details(email: str, db: Session = Depends(get_db),
    user: dict = Depends(authenticate_user),):
    payments_sent = (
        db.query(Paymentdetail)
        .filter(Paymentdetail.from_email == email)
        .order_by(Paymentdetail.created_at.desc())
        .all()
    )
    payments_received = (
        db.query(Paymentdetail)
        .filter(Paymentdetail.to_email == email)
        .order_by(Paymentdetail.created_at.desc())
        .all()
    )

    total_sent = sum(payment.amount for payment in payments_sent)
    total_received = sum(payment.amount for payment in payments_received)
    
    logger.info("Payment History Get Successfully")

    return {
        "total_sent": total_sent,
        "total_received": total_received,
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
