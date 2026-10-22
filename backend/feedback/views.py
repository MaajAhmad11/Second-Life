from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from .models import Feedback
from .serializers import FeedbackSerializer
from connections.models import Connection
from services.email_service import send_platform_email
class FeedbackListCreateView(APIView):
    permission_classes=[permissions.IsAuthenticated]
    def get(self,request,connection_id):
        try: c=Connection.objects.get(pk=connection_id)
        except Connection.DoesNotExist: return Response({'error':'Connection not found.'},status=404)
        if request.user.role!='ADMIN' and request.user.id not in [c.donor_id,c.receiver_id]: return Response({'error':'Permission denied.'},status=403)
        return Response(FeedbackSerializer(c.feedback.select_related('author'),many=True).data)
    def post(self,request,connection_id):
        try: c=Connection.objects.select_related('donor','receiver','donation').get(pk=connection_id)
        except Connection.DoesNotExist: return Response({'error':'Connection not found.'},status=404)
        if request.user.role!='ADMIN' and request.user.id not in [c.donor_id,c.receiver_id]: return Response({'error':'Permission denied.'},status=403)
        if c.status!='COMPLETED': return Response({'error':'Feedback is available after the donation is completed.'},status=400)
        if Feedback.objects.filter(connection=c,author=request.user).exists(): return Response({'error':'You have already submitted feedback for this exchange.'},status=400)
        try: rating=int(request.data.get('rating',5))
        except (TypeError,ValueError): rating=5
        rating=max(1,min(5,rating))
        fb=Feedback.objects.create(connection=c,author=request.user,rating=rating,comment=str(request.data.get('comment','')).strip())
        other=c.receiver if request.user.id==c.donor_id else c.donor
        send_platform_email(other.email,'Second Life - Feedback Received',f'''Hello {other.name},

{request.user.name} has submitted feedback about the completed donation "{c.donation.title}".

Rating: {rating}/5
Comment: {fb.comment or 'No written comment was provided.'}

Thank you for being part of Second Life.

Regards,
Second Life Team''')
        return Response(FeedbackSerializer(fb).data,status=201)
