from django.http import Http404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, AllowAny
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from site_config.models import HeroSection
from site_config.serializers import HeroSectionPublicSerializer, HeroSectionAdminSerializer


class HeroSectionPublicView(generics.RetrieveAPIView):
    """
    Endpoint público para obter a hero section ativa.
    Sem autenticação necessária.
    Cache de 1 hora (3600 segundos).
    """
    serializer_class = HeroSectionPublicSerializer
    permission_classes = [AllowAny]
    
    @method_decorator(cache_page(60 * 60))  # Cache de 1 hora
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_object(self):
        hero = HeroSection.objects.filter(is_active=True).first()
        if not hero:
            raise Http404("Hero section não encontrada.")
        return hero


class HeroSectionListCreateView(generics.ListCreateAPIView):
    """
    Para administradores: listar todas as hero sections e criar novas.
    """
    queryset = HeroSection.objects.all().order_by('-id')
    serializer_class = HeroSectionAdminSerializer
    permission_classes = [IsAdminUser]


class HeroSectionDetailUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    Para administradores: recuperar, atualizar ou deletar uma hero section específica.
    """
    queryset = HeroSection.objects.all()
    serializer_class = HeroSectionAdminSerializer
    permission_classes = [IsAdminUser]


class HeroSectionActivateView(generics.GenericAPIView):
    """
    Para administradores: ativar uma hero section específica
    e desativar as demais.
    """
    queryset = HeroSection.objects.all()
    serializer_class = HeroSectionAdminSerializer
    permission_classes = [IsAdminUser]
    
    def post(self, request, pk):
        try:
            hero = HeroSection.objects.get(pk=pk)
        except HeroSection.DoesNotExist:
            return Response(
                {"detail": "Hero section não encontrada."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        HeroSection.objects.exclude(pk=pk).update(is_active=False)
        
        hero.is_active = True
        hero.save()
        
        return Response(
            self.get_serializer(hero).data,
            status=status.HTTP_200_OK
        )